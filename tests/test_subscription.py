"""Account connection without using a real account or network."""
import io
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_data = tempfile.TemporaryDirectory(prefix="pc-subscription-test-")
os.environ.update(REFORMCUT_DATA=_data.name, DATABASE_URL="", REFORMCUT_ACCOUNTS="0",
                  REFORMCUT_FETCH_MODEL="0", REFORMCUT_UPDATE_CHECK="0", REFORMCUT_AI_PROVIDER="gemini",
                  REFORMCUT_AI_MODELS="", REFORMCUT_AI_KEY="", REFORMCUT_AI_KEY_FILE="",
                  REFORMCUT_PUBLIC_URL="http://127.0.0.1:8765")
from studio import codex
try:
    from studio import subscription
except ImportError:
    subscription = None


class DiscoveryTests(unittest.TestCase):
    def test_registered_windows_app_is_found_without_codex_on_path(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "app" / "resources" / "codex.exe"
            binary.parent.mkdir(parents=True)
            binary.touch()
            reply = subprocess.CompletedProcess([], 0, directory + "\n", "")
            with patch.object(codex.shutil, "which", return_value=None), patch.object(sys, "platform", "win32"), \
                 patch.object(codex.subprocess, "run", return_value=reply), \
                 patch.object(codex.subprocess, "CREATE_NO_WINDOW", 0, create=True), \
                 patch.dict(os.environ, {"REFORMCUT_CODEX_COMMAND": "", "ProgramFiles": directory}):
                self.assertEqual([str(Path(c).resolve()) for c in codex.command()], [str(Path(binary).resolve())])


class FakeRPC:
    account = {"type": "chatgpt", "email": "owner@example.com", "planType": "plus", "accessToken": "secret"}
    instances = []

    def __init__(self):
        self.events = queue.Queue()
        self.closed = False
        self.calls = []
        self.__class__.instances.append(self)

    def request(self, method, params=None, timeout=10):
        self.calls.append((method, params))
        if method == "account/read":
            return {"account": self.account}
        if method == "account/login/start":
            return {"type": "chatgpt", "loginId": "login-one", "authUrl": "https://auth.openai.com/authorize?state=test"}
        return {}

    def close(self):
        self.closed = True


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(subscription, "The subscription connection module must exist")
        self.rpc = patch.object(subscription, "RPC", FakeRPC).start()
        patch.object(codex, "command", return_value=["codex.exe"]).start()
        FakeRPC.account = {"type": "chatgpt", "email": "owner@example.com", "planType": "plus", "accessToken": "secret"}
        FakeRPC.instances = []
        self.connection = subscription.Connection()
        self.addCleanup(self.connection.close)
        self.addCleanup(patch.stopall)

    def test_account_identity_is_public_but_tokens_never_leave_backend(self):
        result = self.connection.status(refresh=True)
        self.assertEqual(result["state"], "connected")
        self.assertEqual(result["account"], {"email": "owner@example.com", "plan": "plus"})
        self.assertNotIn("secret", json.dumps(result))
        self.assertTrue(FakeRPC.instances[-1].closed)

    def test_api_only_or_absent_account_is_disconnected(self):
        for account in (None, {"type": "apiKey", "apiKey": "secret"}):
            FakeRPC.account = account
            result = self.connection.status(refresh=True)
            self.assertEqual(result["state"], "disconnected")
            self.assertIsNone(result["account"])
            self.assertNotIn("secret", json.dumps(result))

    def test_connect_starts_official_browser_flow_and_repeated_click_reuses_it(self):
        FakeRPC.account = None
        result = self.connection.start()
        self.assertEqual(result["state"], "pending")
        self.assertTrue(result["auth_url"].startswith("https://auth.openai.com/"))
        client = FakeRPC.instances[-1]
        self.assertEqual(client.calls[-1], ("account/login/start", {"type": "chatgpt"}))
        self.assertEqual(self.connection.start()["auth_url"], result["auth_url"])
        self.assertEqual(sum(m == "account/login/start" for m, _ in client.calls), 1)

    def test_success_requires_a_matching_login_notification(self):
        self.connection.start()
        client = FakeRPC.instances[-1]
        client.events.put({"method": "account/login/completed", "params": {"loginId": "other", "success": True}})
        self.assertEqual(self.connection.status()["state"], "pending")
        client.events.put({"method": "account/login/completed", "params": {"loginId": "login-one", "success": True}})
        result = self.connection.status()
        self.assertEqual(result["state"], "connected")
        self.assertIsNone(result.get("auth_url"))
        self.assertTrue(client.closed)

    def test_cancel_only_cancels_our_pending_login_not_the_shared_account(self):
        self.connection.start()
        client = FakeRPC.instances[-1]
        self.connection.cancel()
        self.assertIn(("account/login/cancel", {"loginId": "login-one"}), client.calls)
        self.assertFalse(any(method == "account/logout" for method, _ in client.calls))
        self.assertTrue(client.closed)

    def test_failed_login_is_safe_and_can_be_retried(self):
        self.connection.start()
        client = FakeRPC.instances[-1]
        client.events.put({"method": "account/login/completed", "params": {
            "loginId": "login-one", "success": False, "error": "secret bearer token"}})
        result = self.connection.status()
        self.assertEqual(result["state"], "error")
        self.assertNotIn("secret", json.dumps(result))
        self.assertTrue(client.closed)
        self.assertEqual(self.connection.start()["state"], "pending")

    def test_login_expiry_closes_the_process(self):
        FakeRPC.account = None
        self.connection.start()
        client = FakeRPC.instances[-1]
        with patch.object(subscription.time, "monotonic", return_value=10**12):
            self.assertEqual(self.connection.status()["state"], "error")
        self.assertTrue(client.closed)

    def test_old_expiry_callback_cannot_close_a_new_login(self):
        self.connection.start()
        old = FakeRPC.instances[-1]
        self.connection.cancel()
        self.connection.start()
        current = FakeRPC.instances[-1]
        self.connection._expire(old, "login-one")
        self.assertFalse(current.closed)
        self.assertEqual(self.connection.status()["state"], "pending")

    def test_completed_login_is_recognized_after_page_has_been_closed(self):
        self.connection.start()
        client = FakeRPC.instances[-1]
        client.events.put({"method": "account/login/completed", "params": {"loginId": "login-one", "success": True}})
        with patch.object(subscription.time, "monotonic", return_value=10**12):
            self.assertEqual(self.connection.status()["state"], "connected")

    def test_pending_login_expires_without_a_page_poll(self):
        with patch.object(subscription, "LOGIN_SECONDS", 0.03, create=True):
            self.connection.start()
            client = FakeRPC.instances[-1]
            until = time.monotonic() + 1
            while not client.closed and time.monotonic() < until:
                time.sleep(0.01)
            self.assertTrue(client.closed)

    def test_unexpected_login_destination_is_rejected(self):
        original = FakeRPC.request
        def request(client, method, params=None, timeout=10):
            if method == "account/login/start":
                return {"loginId": "one", "authUrl": "https://evil.example/login"}
            return original(client, method, params, timeout)
        with patch.object(FakeRPC, "request", request):
            with self.assertRaises(codex.CodexError):
                self.connection.start()
        self.assertTrue(FakeRPC.instances[-1].closed)

    def test_catalog_reads_all_pages_and_normalizes_model_efforts(self):
        pages = {None: {"data": [{"id": "one", "model": "model-one", "displayName": "Model One", "isDefault": True,
                "defaultReasoningEffort": "medium", "supportedReasoningEfforts": [
                    {"reasoningEffort": "low"}, {"reasoningEffort": "medium"}, {"reasoningEffort": "xhigh"}]}], "nextCursor": "next"},
                 "next": {"data": [{"model": "model-two", "displayName": "Model Two", "supportedReasoningEfforts": [{"reasoningEffort": "high"}]},
                                   {"model": "hidden", "hidden": True}], "nextCursor": None}}
        original = FakeRPC.request
        def request(client, method, params=None, timeout=10):
            if method == "model/list":
                client.calls.append((method, params))
                return pages[params.get("cursor")]
            return original(client, method, params, timeout)
        self.assertTrue(hasattr(self.connection, "catalog"), "The model catalog must be available")
        with patch.object(FakeRPC, "request", request):
            result = self.connection.catalog(refresh=True)
        self.assertEqual([m["id"] for m in result], ["model-one", "model-two"])
        self.assertEqual(result[0]["efforts"], ["low", "medium", "xhigh"])
        self.assertEqual(result[0]["default_effort"], "medium")
        self.assertTrue(result[0]["is_default"])
        self.assertTrue(FakeRPC.instances[-1].closed)

    def test_failed_refresh_does_not_leave_previous_accounts_catalog_cached(self):
        original = FakeRPC.request
        def request(client, method, params=None, timeout=10):
            if method == "model/list":
                return {"data": [{"model": "model-one", "supportedReasoningEfforts": [{"reasoningEffort": "low"}]}]}
            return original(client, method, params, timeout)
        with patch.object(FakeRPC, "request", request):
            self.connection.catalog(refresh=True)
            FakeRPC.account = None
            with self.assertRaises(codex.CodexError):
                self.connection.catalog(refresh=True)
            with self.assertRaises(codex.CodexError):
                self.connection.catalog()


class RPCTests(unittest.TestCase):
    def test_stdio_initialization_account_response_and_process_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "rpc.py"
            script.write_text('import sys,json\nfor line in sys.stdin:\n m=json.loads(line)\n if "id" in m: print(json.dumps({"id":m["id"],"result":{"account":{"type":"chatgpt","email":"test@example.com","planType":"plus"}}}),flush=True)\n', encoding="utf-8")
            with patch.object(codex, "command", return_value=[sys.executable, str(script)]):
                client = subscription.RPC()
                try:
                    self.assertEqual(client.request("account/read")["account"]["email"], "test@example.com")
                finally:
                    client.close()
                self.assertIsNotNone(client.process.poll())
                self.assertFalse(client.reader.is_alive())


class RouteTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        from studio import db
        db.engine.dispose()

    def setUp(self):
        from fastapi.testclient import TestClient
        from studio import ai, config, db, server
        self.ai = ai
        self.config, self.server = config, server
        db.init()
        self.client = TestClient(server.app, base_url="http://127.0.0.1:8765")
        self.origin = {"Origin": "http://127.0.0.1:8765"}
        self.state = {"state": "connected", "installed": True, "account": {"email": "owner@example.com", "plan": "plus"},
                      "auth_url": None, "error": ""}
        self.status = patch.object(subscription.connection, "status", return_value=self.state).start()
        self.start = patch.object(subscription.connection, "start", return_value={**self.state, "state": "pending",
                              "auth_url": "https://auth.openai.com/authorize?state=test"}).start()
        self.cancel = patch.object(subscription.connection, "cancel", return_value=self.state).start()
        patch.object(ai, "provider", return_value="codex").start()
        patch.object(ai, "models", return_value=["default"]).start()
        self.test_model = patch.object(ai, "test_codex", create=True, return_value={"ok": True, "model": "default", "tokens": 2}).start()
        self.save = patch.object(ai, "save", return_value={}).start()
        self.catalog = patch.object(subscription.connection, "catalog", create=True, return_value=[
            {"id": "model-one", "label": "Model One", "is_default": True, "default_effort": "low", "efforts": ["low", "medium", "xhigh"]},
            {"id": "new-model", "label": "New Model", "is_default": False, "default_effort": "low", "efforts": ["low", "high"]}]).start()
        self.addCleanup(patch.stopall)

    def test_subscription_status_and_connection_routes(self):
        response = self.client.get("/api/ai/subscription?refresh=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["account"]["email"], "owner@example.com")
        self.assertTrue(response.json()["active"])
        self.assertEqual(self.client.post("/api/ai/subscription/connect", headers=self.origin).json()["state"], "pending")
        self.assertEqual(self.client.post("/api/ai/subscription/cancel", headers=self.origin).status_code, 200)

    def test_cross_site_login_launch_is_refused(self):
        response = self.client.post("/api/ai/subscription/connect", headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)
        self.start.assert_not_called()

    def test_testing_the_active_model_does_not_shadow_environment_settings(self):
        result = self.client.post("/api/ai/subscription/use", headers=self.origin, json={"models": "default"})
        self.assertEqual(result.status_code, 200)
        self.save.assert_not_called()

    def test_failed_activation_preserves_the_existing_provider_and_key(self):
        with patch.object(self.ai, "provider", return_value="gemini"):
            self.test_model.side_effect = codex.CodexError("The subscription did not answer.")
            result = self.client.post("/api/ai/subscription/use", headers=self.origin, json={"models": "default"})
            self.assertEqual(result.status_code, 502)
            self.save.assert_not_called()

    def test_successful_model_change_is_saved_after_validation(self):
        result = self.client.post("/api/ai/subscription/use", headers=self.origin, json={"models": "new-model"})
        self.assertEqual(result.status_code, 200)
        self.save.assert_called_once_with("codex", ["new-model"], reasoning_effort="")

    def test_catalog_route_returns_actual_model_choices(self):
        result = self.client.get("/api/ai/subscription/models?refresh=1")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["models"][0]["efforts"], ["low", "medium", "xhigh"])

    def test_selected_effort_is_tested_and_saved(self):
        result = self.client.post("/api/ai/subscription/use", headers=self.origin,
                                  json={"models": "model-one", "reasoning_effort": "xhigh"})
        self.assertEqual(result.status_code, 200)
        self.test_model.assert_called_once_with(["model-one"], reasoning_effort="xhigh")
        self.save.assert_called_once_with("codex", ["model-one"], reasoning_effort="xhigh")
        self.catalog.assert_called_once_with(refresh=True)

    def test_legacy_codex_save_validates_inherited_effort_before_writing(self):
        with patch.object(self.ai, "current", return_value={"reasoning_effort": "xhigh"}):
            result = self.client.put("/api/ai", headers=self.origin, json={"provider": "codex", "models": "new-model"})
        self.assertEqual(result.status_code, 400)
        self.test_model.assert_not_called()
        self.save.assert_not_called()

    def test_unsupported_effort_is_rejected_before_model_call_or_save(self):
        result = self.client.post("/api/ai/subscription/use", headers=self.origin,
                                  json={"models": "new-model", "reasoning_effort": "xhigh"})
        self.assertEqual(result.status_code, 400)
        self.test_model.assert_not_called()
        self.save.assert_not_called()

    def test_unavailable_model_is_rejected_before_model_call(self):
        result = self.client.post("/api/ai/subscription/use", headers=self.origin,
                                  json={"models": "not-available", "reasoning_effort": "low"})
        self.assertEqual(result.status_code, 400)
        self.test_model.assert_not_called()

    def test_invalid_model_is_rejected_before_testing(self):
        result = self.client.post("/api/ai/subscription/use", headers=self.origin, json={"models": 'bad model; "'})
        self.assertEqual(result.status_code, 400)
        self.test_model.assert_not_called()

    def test_connection_routes_require_signed_in_admin_when_accounts_are_enabled(self):
        with patch.object(self.config, "ACCOUNTS", True):
            for method, url in (("GET", "/api/ai/subscription"), ("GET", "/api/ai/subscription/models"), ("POST", "/api/ai/subscription/connect"),
                                ("POST", "/api/ai/subscription/cancel"), ("POST", "/api/ai/subscription/use")):
                self.assertIn(self.client.request(method, url, headers=self.origin).status_code, (401, 403))


if __name__ == "__main__":
    unittest.main(verbosity=2)
