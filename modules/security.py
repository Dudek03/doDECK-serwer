import os
import json
import secrets
import hmac
import hashlib
import time
import socket
from functools import wraps
from typing import Optional, Dict, Any, Callable
from flask import request, jsonify, Response
from modules.paths import get_config_path

TOKEN_FILE: str = get_config_path("trusted_devices.json")
SEEN_SIGNATURES: Dict[str, float] = {}  # signature: expiration_time


def is_localhost(remote_addr: Optional[str]) -> bool:
    """Checks whether the request originates from the local host machine."""
    if not remote_addr:
        return False
    return (
        remote_addr in ("127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1")
        or remote_addr.endswith("127.0.0.1")
    )


def require_localhost(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator blocking access to sensitive endpoints for devices outside localhost."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not is_localhost(request.remote_addr):
            return jsonify(
                {"error": "Unauthorized. Access allowed only from local host machine (PC)."}
            ), 403
        return f(*args, **kwargs)

    return decorated_function


def get_local_ip() -> str:
    """Retrieves local Wi-Fi / LAN IP address of the server."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = str(s.getsockname()[0])
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_or_create_secret() -> str:
    """Retrieves existing secret key or generates a new 64-char key and securely saves it."""
    token_file = get_config_path("trusted_devices.json")
    if os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                sec = data.get("secret")
                if sec and isinstance(sec, str) and len(sec) == 64:
                    return sec
        except Exception:
            pass

    new_secret = secrets.token_hex(32)
    try:
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "w", encoding="utf-8") as f:
            json.dump({"secret": new_secret}, f, indent=4)
    except Exception as e:
        print(f"[WARN] [Security] Error saving secret key to file: {e}")
    return new_secret


def rotate_secret() -> str:
    """Generates a new secret key, invalidating previously paired devices."""
    token_file = get_config_path("trusted_devices.json")
    new_secret = secrets.token_hex(32)
    try:
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        with open(token_file, "w", encoding="utf-8") as f:
            json.dump({"secret": new_secret}, f, indent=4)
    except Exception as e:
        print(f"[WARN] [Security] Error saving new secret key: {e}")
    return new_secret


def _is_signature_replayed(signature: str, current_time: float) -> bool:
    """Detects reuse of the same signature within the time window (replay attack protection)."""
    expired = [sig for sig, exp in SEEN_SIGNATURES.items() if exp < current_time]
    for sig in expired:
        del SEEN_SIGNATURES[sig]

    if signature in SEEN_SIGNATURES:
        return True

    SEEN_SIGNATURES[signature] = current_time + 15
    return False


def verify_socket_payload(data_dict: Any, action_type: str) -> bool:
    """
    Verifies HMAC signature for incoming Socket.IO events.
    data_dict: Dictionary received from client (must contain 'timestamp' and 'signature')
    action_type: 'action' (for trigger_action) or 'macro' (for trigger_macro)
    """
    if not isinstance(data_dict, dict):
        return False

    signature = data_dict.get("signature")
    timestamp = data_dict.get("timestamp")

    if not signature or not timestamp:
        print("[Security] Rejected: Missing signature or timestamp.")
        return False

    current_time = time.time()
    try:
        ts = float(timestamp)
        # Reject requests older than 10s or ahead by more than 10s
        if abs(current_time - ts) > 10:
            print("[Security] Rejected: Timestamp out of bounds (Replay/Skew).")
            return False
    except (ValueError, TypeError):
        return False

    # Check memory of unique signatures (replay attack check)
    if _is_signature_replayed(signature, current_time):
        print("[Security] Rejected: Signature replayed (Replay Attack).")
        return False

    if action_type == "action":
        args_data = data_dict.get("args", "")

        if isinstance(args_data, (dict, list)):
            args_str = json.dumps(args_data, separators=(",", ":"), ensure_ascii=False)
        else:
            args_str = str(args_data)

        raw_string = f"{data_dict.get('command', '')}{args_str}{timestamp}"
    elif action_type == "macro":
        steps_str = json.dumps(data_dict.get("steps", []), separators=(",", ":"))
        raw_string = f"{steps_str}{timestamp}"
    else:
        return False

    secret = get_or_create_secret()
    if not secret:
        return False

    expected_signature = hmac.new(
        secret.encode("utf-8"), raw_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(signature, expected_signature):
        return True
    else:
        print("[Security] Rejected: Invalid HMAC signature.")
        return False
