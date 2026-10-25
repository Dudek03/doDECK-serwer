import os
import json
import secrets
import hmac
import hashlib
import time
import socket

TOKEN_FILE = "trusted_devices.json"


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
    """Pobiera istniejący klucz lub generuje nowy, 64-znakowy i zapisuje do pliku."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("secret")

    new_secret = secrets.token_hex(32)
    with open(TOKEN_FILE, "w") as f:
        json.dump({"secret": new_secret}, f)
    return new_secret


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

    # Sprawdzenie Replay Attack (odrzucamy zapytania starsze niż 10 sekund)
    try:
        if time.time() - float(timestamp) > 10:
            print(
                "🔒 [Zabezpieczenia] Odrzucono: Zbyt stare zapytanie (Replay Attack)."
            )
            return False
    except ValueError:
        return False

    # Odtwarzamy oryginalny ciąg znaków, który podpisał frontend
    if action_type == "action":
        # Dla pojedynczej akcji podpisujemy: command + args + timestamp
        raw_string = (
            f"{data_dict.get('command', '')}{data_dict.get('args', '')}{timestamp}"
        )
    elif action_type == "macro":
        # Dla makra podpisujemy JSONa ze schodkami + timestamp
        # Używamy separators=(',', ':') by pozbyć się spacji, co ułatwia zgodność z JavaScript
        steps_str = json.dumps(data_dict.get("steps", []), separators=(",", ":"))
        raw_string = f"{steps_str}{timestamp}"
    else:
        return False

    secret = get_or_create_secret().encode("utf-8")
    expected_signature = hmac.new(
        secret, raw_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(signature, expected_signature):
        return True
    else:
        print("🔒 [Zabezpieczenia] Odrzucono: Błędny podpis HMAC.")
        return False
