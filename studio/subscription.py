"""Connect a ChatGPT account using Codex's official account protocol. Codex keeps all credentials."""
import atexit
import json
import queue
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

from . import codex

FAILED = "The ChatGPT connection did not finish. Try connecting again."
LOGIN_SECONDS = 600


class RPC:
    """A small, bounded stdio client used only for account operations; it never starts an agent turn."""
    def __init__(self):
        args = codex.command()
        if not args:
            raise codex.CodexError(codex.INSTALL)
        args += ["app-server", "--listen", "stdio://"]
        for feature in codex.DISABLED_FEATURES:
            args += ["-c", f"features.{feature}=false"]
        self.events = queue.Queue()
        self.pending = {}
        self.lock = threading.Lock()
        self.next_id = 0
        self.closed = False
        try:
            self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                            text=True, encoding="utf-8", errors="replace", env=codex._env(),
                                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        except OSError:
            raise codex.CodexError(codex.INSTALL) from None
        self.reader = threading.Thread(target=self._read, daemon=True, name="peakcut-codex-account")
        self.reader.start()
        try:
            self.request("initialize", {"clientInfo": {"name": "peakcut", "title": "PeakCut", "version": "1"}})
            self._send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def _send(self, message):
        try:
            self.process.stdin.write(json.dumps(message) + "\n")
            self.process.stdin.flush()
        except (OSError, ValueError):
            raise codex.CodexError(FAILED) from None

    def _read(self):
        try:
            for line in self.process.stdout:
                message = json.loads(line)
                if not isinstance(message, dict):
                    break
                with self.lock:
                    target = self.pending.get(message.get("id"))
                if target is not None:
                    target.put(message)
                elif message.get("method"):
                    self.events.put(message)
        except (OSError, ValueError):
            pass
        finally:
            with self.lock:
                waiting = list(self.pending.values())
            for target in waiting:
                target.put({"error": True})
            self.events.put({"method": "connection/closed"})

    def request(self, method, params=None, timeout=10):
        target = queue.Queue()
        with self.lock:
            if self.closed:
                raise codex.CodexError(FAILED)
            self.next_id += 1
            request_id = self.next_id
            self.pending[request_id] = target
            self._send({"id": request_id, "method": method, "params": params or {}})
        try:
            message = target.get(timeout=timeout)
            if "error" in message or not isinstance(message.get("result"), dict):
                raise codex.CodexError(FAILED)
            return message["result"]
        except queue.Empty:
            self.close()
            raise codex.CodexError("Codex did not respond. Refresh the connection or try again.") from None
        finally:
            with self.lock:
                self.pending.pop(request_id, None)

    def close(self):
        self.closed = True
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.reader.join(timeout=1)
        self.process.stdin.close()
        self.process.stdout.close()


def _account(result):
    value = result.get("account")
    if not isinstance(value, dict) or value.get("type") != "chatgpt":
        return None
    return {"email": str(value.get("email") or "")[:254], "plan": str(value.get("planType") or "")[:60]}


class Connection:
    def __init__(self):
        self.lock = threading.RLock()
        self.client = None
        self.login_id = None
        self.auth_url = None
        self.deadline = 0
        self.cached = None
        self.cached_at = 0
        self.expiry = None

    def _state(self, state, account=None, error=""):
        return {"state": state, "installed": bool(codex.command()), "account": account,
                "auth_url": self.auth_url if state == "pending" else None, "error": error}

    def _stop(self):
        if self.expiry:
            self.expiry.cancel()
            self.expiry = None
        if self.client:
            self.client.close()
        self.client, self.login_id, self.auth_url = None, None, None
        self.deadline = 0

    def _expire(self, client, login_id):
        with self.lock:
            if self.client is client and self.login_id == login_id:
                self.status(refresh=True)

    def _remember(self, state):
        self.cached, self.cached_at = state, time.monotonic()
        return dict(state)

    def status(self, refresh=False):
        with self.lock:
            if self.client:
                while True:
                    try:
                        event = self.client.events.get_nowait()
                    except queue.Empty:
                        if time.monotonic() >= self.deadline:
                            try:
                                account = _account(self.client.request("account/read", {"refreshToken": False}, timeout=5))
                            except codex.CodexError:
                                account = None
                            self._stop()
                            codex._status_cache.clear()
                            return self._remember(self._state("connected" if account else "error", account,
                                      error="The connection link expired." + (" The current Codex account is still connected." if account else " Connect ChatGPT again.")))
                        return self._state("pending")
                    if event.get("method") == "connection/closed":
                        self._stop()
                        return self._remember(self._state("error", error=FAILED))
                    params = event.get("params") or {}
                    if event.get("method") == "account/login/completed" and params.get("loginId") == self.login_id:
                        if not params.get("success"):
                            self._stop()
                            return self._remember(self._state("error", error=FAILED))
                        self._stop()
                        self.cached = None
                        codex._status_cache.clear()
                        break
            if not codex.command():
                return self._state("unavailable", error=codex.INSTALL)
            if not refresh and self.cached and time.monotonic() - self.cached_at < 10:
                return dict(self.cached)
            client = None
            try:
                client = RPC()
                account = _account(client.request("account/read", {"refreshToken": False}))
                return self._remember(self._state("connected" if account is not None else "disconnected", account))
            except codex.CodexError as error:
                return self._remember(self._state("error", error=str(error)))
            finally:
                if client:
                    client.close()

    def start(self):
        with self.lock:
            if self.client:
                current = self.status()
                if current["state"] == "pending":
                    return current
            client = RPC()
            try:
                result = client.request("account/login/start", {"type": "chatgpt"})
                url = result.get("authUrl") or ""
                parsed = urlparse(url)
                if parsed.scheme != "https" or parsed.hostname not in {"auth.openai.com", "chatgpt.com"} or \
                   parsed.username or parsed.password or parsed.port not in (None, 443) or not result.get("loginId"):
                    raise codex.CodexError("Codex did not return an official ChatGPT login link. Update Codex and try again.")
                self.client, self.login_id, self.auth_url = client, result["loginId"], url
                self.deadline = time.monotonic() + LOGIN_SECONDS
                self.expiry = threading.Timer(LOGIN_SECONDS, self._expire, args=(client, self.login_id))
                self.expiry.daemon = True
                self.expiry.start()
                self.cached = None
                return self._state("pending")
            except Exception:
                client.close()
                raise

    def cancel(self):
        with self.lock:
            try:
                if self.client:
                    self.client.request("account/login/cancel", {"loginId": self.login_id}, timeout=5)
            finally:
                self._stop()
                self.cached = None
            return self.status(refresh=True)

    def close(self):
        with self.lock:
            self._stop()


connection = Connection()
atexit.register(connection.close)
