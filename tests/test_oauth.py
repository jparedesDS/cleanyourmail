from __future__ import annotations

import os
import stat
import unittest
from unittest.mock import patch

from helpers import TempDir

import oauth_ms


DEVICE = {
    "device_code": "device-secret",
    "user_code": "ABCD-EFGH",
    "verification_uri": "https://microsoft.com/devicelogin",
    "expires_in": 900,
    "interval": 5,
    "message": "Open the page and enter the code.",
}

TOKEN = {
    "access_token": "access-secret",
    "refresh_token": "refresh-secret",
    "expires_in": 3600,
    "scope": oauth_ms.DEFAULT_SCOPE,
}


class OAuthTest(unittest.TestCase):
    def test_start_device_flow(self):
        with patch("oauth_ms._post", return_value=(200, DEVICE)) as post:
            device = oauth_ms.start_device_flow("client-id", login_hint="me@outlook.com")
        self.assertEqual(device.user_code, "ABCD-EFGH")
        self.assertEqual(device.verification_uri, "https://microsoft.com/devicelogin")
        data = post.call_args.args[1]
        self.assertEqual(data["login_hint"], "me@outlook.com")
        self.assertEqual(data["client_id"], "client-id")

    def test_poll_waits_for_pending_then_succeeds(self):
        replies = [(400, {"error": "authorization_pending"}), (200, TOKEN)]
        with patch("oauth_ms._post", side_effect=replies):
            token = oauth_ms.poll_for_token("device", "client", 5, 900,
                                            sleep=lambda _seconds: None, clock=lambda: 0)
        self.assertEqual(token.access_token, "access-secret")
        self.assertEqual(token.refresh_token, "refresh-secret")

    def test_poll_slow_down_increases_interval(self):
        replies = [
            (400, {"error": "authorization_pending"}),
            (400, {"error": "slow_down"}),
            (200, TOKEN),
        ]
        sleeps: list[int] = []
        with patch("oauth_ms._post", side_effect=replies):
            oauth_ms.poll_for_token("device", "client", 5, 900,
                                    sleep=sleeps.append, clock=lambda: 0)
        self.assertEqual(sleeps, [5, 5, 10])

    def test_poll_expired(self):
        clock = iter([0, 1000])
        with self.assertRaises(oauth_ms.OAuthError) as caught:
            oauth_ms.poll_for_token("device", "client", 5, 900,
                                    sleep=lambda _seconds: None, clock=lambda: next(clock))
        self.assertIn("expired", str(caught.exception))

    def test_poll_declined(self):
        with patch("oauth_ms._post", return_value=(400, {"error": "authorization_declined"})):
            with self.assertRaises(oauth_ms.OAuthError) as caught:
                oauth_ms.poll_for_token("device", "client", 5, 900,
                                        sleep=lambda _seconds: None, clock=lambda: 0)
        self.assertIn("declined", str(caught.exception))

    def test_refresh_keeps_old_refresh_token(self):
        payload = {"access_token": "new-access", "expires_in": 3600}
        with patch("oauth_ms._post", return_value=(200, payload)):
            token = oauth_ms.refresh_access_token("old-refresh", "client")
        self.assertEqual(token.access_token, "new-access")
        self.assertEqual(token.refresh_token, "old-refresh")

    def test_refresh_invalid_grant_asks_to_connect_again(self):
        payload = {"error": "invalid_grant", "error_description": "revoked"}
        with patch("oauth_ms._post", return_value=(400, payload)):
            with self.assertRaises(oauth_ms.OAuthError) as caught:
                oauth_ms.refresh_access_token("old-refresh", "client")
        self.assertIn("connect outlook", str(caught.exception))

    def test_store_round_trip_without_access_token(self):
        with TempDir() as temp:
            path = temp / "oauth.json"
            token = oauth_ms.Token("access-secret", "refresh-secret", 3600)
            oauth_ms.save_token("client-id", token, email="me@outlook.com", path=path)
            entry = oauth_ms.stored_token(path)
            self.assertEqual(entry["refresh_token"], "refresh-secret")
            self.assertEqual(entry["client_id"], "client-id")
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("access-secret", text)
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_access_token_requires_sign_in(self):
        with TempDir() as temp:
            path = temp / "missing.json"
            with self.assertRaises(oauth_ms.OAuthError) as caught:
                oauth_ms.access_token("client-id", path=path)
        self.assertIn("connect outlook", str(caught.exception))

    def test_access_token_rejects_other_account(self):
        with TempDir() as temp:
            path = temp / "oauth.json"
            oauth_ms.save_token("client", oauth_ms.Token("a", "r", 3600),
                                email="me@outlook.com", path=path)
            with self.assertRaises(oauth_ms.OAuthError) as caught:
                oauth_ms.access_token("client", email="other@outlook.com", path=path)
        self.assertIn("different account", str(caught.exception))

    def test_access_token_rejects_different_client(self):
        with TempDir() as temp:
            path = temp / "oauth.json"
            oauth_ms.save_token("old-client", oauth_ms.Token("a", "r", 3600),
                                email="me@outlook.com", path=path)
            with self.assertRaises(oauth_ms.OAuthError) as caught:
                oauth_ms.access_token("new-client", email="me@outlook.com", path=path)
        self.assertIn("different Microsoft application", str(caught.exception))

    def test_access_token_uses_stored_client_and_saves_rotation(self):
        with TempDir() as temp:
            path = temp / "oauth.json"
            oauth_ms.save_token("stored-client", oauth_ms.Token("old", "old-refresh", 3600),
                                email="me@outlook.com", path=path)
            rotated = oauth_ms.Token("fresh", "new-refresh", 3600)
            with patch("oauth_ms.refresh_access_token", return_value=rotated) as refresh:
                value = oauth_ms.access_token("stored-client", email="me@outlook.com", path=path)
            self.assertEqual(value, "fresh")
            self.assertEqual(refresh.call_args.args[0], "old-refresh")
            self.assertEqual(refresh.call_args.args[1], "stored-client")
            self.assertEqual(oauth_ms.stored_token(path)["refresh_token"], "new-refresh")

    def test_client_id_from_env(self):
        with patch.dict(os.environ, {"CYM_MS_CLIENT_ID": "  env-client  "}):
            self.assertEqual(oauth_ms.client_id_from_env(), "env-client")

    def test_account_from_id_token(self):
        import base64
        import json

        payload = {"preferred_username": "me@outlook.com"}
        encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        self.assertEqual(oauth_ms.account_from_id_token(f"x.{encoded}.y"), "me@outlook.com")
        self.assertEqual(oauth_ms.account_from_id_token(""), "")
        self.assertEqual(oauth_ms.account_from_id_token("not-a-token"), "")

    def test_error_description_is_truncated(self):
        error = oauth_ms._describe_error(
            {"error": "invalid_request", "error_description": "x" * 1000}, 400)
        self.assertLessEqual(len(str(error)), 400)
        self.assertNotIn("\n", str(error))


if __name__ == "__main__":
    unittest.main()
