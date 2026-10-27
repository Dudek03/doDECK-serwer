import os
import json
import secrets
import hmac
import hashlib
import time
import socket
from functools import wraps
from flask import request, jsonify

TOKEN_FILE = "trusted_devices.json"
SEEN_SIGNATURES = {}  # signature: expiration_time


def is_localhost(remote_addr):
    """Sprawdza, czy zapytanie pochodzi z lokalnej maszyny hosta."""
    return remote_addr in ("127.0.0.1", "::1", "localhost")


def require_localhost(f):
    """Dekorator blokujący dostęp do wrażliwych endpointów dla urządzeń spoza localhosta."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_localhost(request.remote_addr):
            return jsonify(
                {"error": "Brak uprawnień. Dostęp dozwolony tylko z lokalnej maszyny (PC)."}
            ), 403
        return f(*args, **kwargs)

    return decorated_function


def get_local_ip():
    """Pobiera lokalne IP serwera w sieci Wi-Fi"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_or_create_secret():
    """Pobiera istniejący klucz lub generuje nowy, 64-znakowy i bezpiecznie zapisuje do pliku."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                sec = data.get("secret")
                if sec and isinstance(sec, str) and len(sec) == 64:
                    return sec
        except Exception:
            pass

    new_secret = secrets.token_hex(32)
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump({"secret": new_secret}, f)
    except Exception as e:
        print(f"⚠️ [Security] Błąd zapisu klucza do pliku: {e}")
    return new_secret


def rotate_secret():
    """Generuje nowy klucz, unieważniając dotychczas sparowane urządzenia."""
    new_secret = secrets.token_hex(32)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"secret": new_secret}, f)
    return new_secret


def _is_signature_replayed(signature, current_time):
    """Wykrywa ponowne użycie tego samego podpisu w oknie czasowym (ochrona przed replay attack)."""
    expired = [sig for sig, exp in SEEN_SIGNATURES.items() if exp < current_time]
    for sig in expired:
        del SEEN_SIGNATURES[sig]

    if signature in SEEN_SIGNATURES:
        return True

    SEEN_SIGNATURES[signature] = current_time + 15
    return False


def verify_socket_payload(data_dict, action_type):
    """
    Weryfikuje podpis HMAC dla Socket.IO.
    data_dict: Słownik odebrany z frontendu (musi zawierać 'timestamp' i 'signature')
    action_type: 'action' (dla trigger_action) lub 'macro' (dla trigger_macro)
    """
    if not isinstance(data_dict, dict):
        return False

    signature = data_dict.get("signature")
    timestamp = data_dict.get("timestamp")

    if not signature or not timestamp:
        print("🔒 [Zabezpieczenia] Odrzucono: Brak podpisu lub czasu.")
        return False

    current_time = time.time()
    try:
        ts = float(timestamp)
        # Odrzucamy zapytania starsze niż 10s lub wyprzedzające zegar o więcej niż 10s
        if abs(current_time - ts) > 10:
            print("🔒 [Zabezpieczenia] Odrzucono: Zbyt stare lub przyszłe zapytanie (Replay/Skew).")
            return False
    except (ValueError, TypeError):
        return False

    # Sprawdzenie pamięci unikalnych podpisów (odrzucenie powtórzonego pakietu w oknie 10s)
    if _is_signature_replayed(signature, current_time):
        print("🔒 [Zabezpieczenia] Odrzucono: Wykryto powtórzone zapytanie (Replay Attack).")
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
        print("🔒 [Zabezpieczenia] Odrzucono: Błędny podpis HMAC.")
        return False
