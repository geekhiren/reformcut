"""Cookie connection and posting without contacting Instagram."""
import tempfile
import sys
from datetime import datetime, timezone
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from studio import accounts, config, ctx


class InstagramSessionTest(unittest.TestCase):
    def test_connect_store_post_and_disconnect(self):
        client = SimpleNamespace(login_by_sessionid=lambda value: None,
                                 account_info=lambda: SimpleNamespace(pk=123, username="example"),
                                 get_settings=lambda: {"authorization_data": {"sessionid": "secret"}},
                                 clip_upload=lambda path, caption, thumbnail: SimpleNamespace(pk=456, code="abc"))
        with tempfile.TemporaryDirectory() as directory, patch.object(config, "user_dir", return_value=Path(directory)), \
                patch("instagrapi.Client", return_value=client), ctx.as_user("test"):
            acc = accounts.instagram_session_add("secret")
            self.assertNotIn("secret", str(accounts.list_accounts()))
            video = Path(directory) / "clip.mp4"
            video.with_suffix(".jpg").write_bytes(b"cover")
            self.assertEqual(accounts.instagram_upload(acc, video, "caption"),
                             ("456", "https://www.instagram.com/reel/abc/"))
            self.assertIsNone(accounts.instagram_views(acc, "456"))
            accounts.remove(acc["id"])
            self.assertEqual(accounts.list_accounts(), [])

    def test_rejection_does_not_expose_cookie(self):
        with patch("instagrapi.Client", side_effect=RuntimeError("secret")):
            with self.assertRaises(ValueError) as error:
                accounts.instagram_session_add("secret")
            self.assertNotIn("secret", str(error.exception))

    def test_post_found_after_upload_response_fails(self):
        media = SimpleNamespace(pk=456, code="abc", caption_text="caption", taken_at=datetime.now(timezone.utc))
        client = SimpleNamespace(clip_upload=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("response failed")),
                                 user_medias=lambda *a, **k: [media])
        with tempfile.TemporaryDirectory() as directory, patch("instagrapi.Client", return_value=client):
            video = Path(directory) / "clip.mp4"
            video.with_suffix(".jpg").write_bytes(b"cover")
            self.assertEqual(accounts.instagram_upload({"user_id": "123", "session_settings": {"ok": 1}}, video, "caption"),
                             ("456", "https://www.instagram.com/reel/abc/"))

    def test_remote_and_multiuser_refused(self):
        from fastapi import HTTPException
        from studio.server import instagram_session
        remote = SimpleNamespace(client=SimpleNamespace(host="192.0.2.1"))
        local = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        with patch.object(config, "ACCOUNTS", False), patch.object(config, "HOST", "127.0.0.1"):
            with self.assertRaises(HTTPException):
                instagram_session(remote, {"sessionid": "secret"})
        with patch.object(config, "ACCOUNTS", True):
            with self.assertRaises(HTTPException):
                instagram_session(local, {"sessionid": "secret"})


if __name__ == "__main__":
    unittest.main()
