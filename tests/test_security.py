import unittest
from unittest.mock import MagicMock, patch
import json
import time
import hmac
import hashlib
from flask import Flask, jsonify
from modules.security import (
    get_local_ip,
    get_or_create_secret,
    rotate_secret,
    verify_socket_payload,
    is_localhost,
    require_localhost,
    SEEN_SIGNATURES,
)


class TestSecurity(unittest.TestCase):
    def setUp(self):
        SEEN_SIGNATURES.clear()

    def test_is_localhost(self):
        self.assertTrue(is_localhost("127.0.0.1"))
        self.assertTrue(is_localhost("::1"))
        self.assertTrue(is_localhost("localhost"))
        self.assertFalse(is_localhost("192.168.1.50"))
        self.assertFalse(is_localhost("10.0.0.1"))

    def test_require_localhost_decorator(self):
        app = Flask(__name__)

        @app.route("/secret-endpoint")
        @require_localhost
        def secret_view():
            return jsonify({"status": "ok"})

        client = app.test_client()

        # Localhost allowed
        res_local = client.get(
            "/secret-endpoint", environ_base={"REMOTE_ADDR": "127.0.0.1"}
        )
        self.assertEqual(res_local.status_code, 200)

        # Remote forbidden
        res_remote = client.get(
            "/secret-endpoint", environ_base={"REMOTE_ADDR": "192.168.1.100"}
        )
        self.assertEqual(res_remote.status_code, 403)
        self.assertIn("Brak uprawnień", res_remote.get_json()["error"])

    @patch("socket.socket")
    def test_get_local_ip_success(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ["192.168.1.150", 5000]
        mock_socket_cls.return_value = mock_sock

        ip = get_local_ip()
        self.assertEqual(ip, "192.168.1.150")

    @patch("socket.socket")
    def test_get_local_ip_failure_fallback(self, mock_socket_cls):
        mock_socket_cls.side_effect = Exception("Network unreachable")
        ip = get_local_ip()
        self.assertEqual(ip, "127.0.0.1")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open")
    def test_get_or_create_secret_existing(self, mock_open, mock_exists):
        valid_64_char_hex = "a" * 64
        with patch("json.load", return_value={"secret": valid_64_char_hex}):
            secret = get_or_create_secret()
            self.assertEqual(secret, valid_64_char_hex)

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open")
    def test_get_or_create_secret_new(self, mock_open, mock_exists):
        with patch("json.dump") as mock_dump:
            secret = get_or_create_secret()
            self.assertEqual(len(secret), 64)
            mock_dump.assert_called_once()

    @patch("builtins.open")
    def test_rotate_secret(self, mock_open):
        with patch("json.dump") as mock_dump:
            new_sec = rotate_secret()
            self.assertEqual(len(new_sec), 64)
            mock_dump.assert_called_once()

    @patch("modules.security.get_or_create_secret", return_value="my_test_secret")
    def test_verify_socket_payload_action_success(self, mock_secret):
        now = str(time.time())
        command = "hotkey"
        args = "ctrl+c"
        raw_string = f"{command}{args}{now}"
        signature = hmac.new(
            b"my_test_secret", raw_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        payload = {
            "command": command,
            "args": args,
            "timestamp": now,
            "signature": signature,
        }

        self.assertTrue(verify_socket_payload(payload, "action"))

    @patch("modules.security.get_or_create_secret", return_value="my_test_secret")
    def test_verify_socket_payload_macro_success(self, mock_secret):
        now = str(time.time())
        steps = [{"command": "hotkey", "args": "win+d", "delay": 0}]
        steps_str = json.dumps(steps, separators=(",", ":"))
        raw_string = f"{steps_str}{now}"
        signature = hmac.new(
            b"my_test_secret", raw_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        payload = {
            "steps": steps,
            "timestamp": now,
            "signature": signature,
        }

        self.assertTrue(verify_socket_payload(payload, "macro"))

    @patch("modules.security.get_or_create_secret", return_value="my_test_secret")
    def test_verify_socket_payload_expired_timestamp(self, mock_secret):
        expired_ts = str(time.time() - 20)  # 20 seconds ago (> 10s limit)
        payload = {
            "command": "hotkey",
            "args": "ctrl+c",
            "timestamp": expired_ts,
            "signature": "any_signature",
        }
        self.assertFalse(verify_socket_payload(payload, "action"))

    @patch("modules.security.get_or_create_secret", return_value="my_test_secret")
    def test_verify_socket_payload_future_timestamp(self, mock_secret):
        future_ts = str(time.time() + 50)  # 50 seconds in future
        payload = {
            "command": "hotkey",
            "args": "ctrl+c",
            "timestamp": future_ts,
            "signature": "any_signature",
        }
        self.assertFalse(verify_socket_payload(payload, "action"))

    @patch("modules.security.get_or_create_secret", return_value="my_test_secret")
    def test_verify_socket_payload_replay_attack_rejected(self, mock_secret):
        now = str(time.time())
        raw_string = f"hotkeyctrl+c{now}"
        signature = hmac.new(
            b"my_test_secret", raw_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        payload = {
            "command": "hotkey",
            "args": "ctrl+c",
            "timestamp": now,
            "signature": signature,
        }

        # First time succeeds
        self.assertTrue(verify_socket_payload(payload, "action"))

        # Second time with the exact same signature (replayed packet) must be rejected!
        self.assertFalse(verify_socket_payload(payload, "action"))

    @patch("modules.security.get_or_create_secret", return_value="my_test_secret")
    def test_verify_socket_payload_invalid_signature(self, mock_secret):
        now = str(time.time())
        payload = {
            "command": "hotkey",
            "args": "ctrl+c",
            "timestamp": now,
            "signature": "invalid_wrong_hash",
        }
        self.assertFalse(verify_socket_payload(payload, "action"))

    def test_verify_socket_payload_missing_fields(self):
        self.assertFalse(verify_socket_payload({}, "action"))
        self.assertFalse(verify_socket_payload("not_a_dict", "action"))
        self.assertFalse(
            verify_socket_payload({"command": "hotkey"}, "action")
        )
        self.assertFalse(
            verify_socket_payload(
                {"signature": "sig", "timestamp": "invalid_time"}, "action"
            )
        )


if __name__ == "__main__":
    unittest.main()
