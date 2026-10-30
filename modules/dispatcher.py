from flask import Blueprint, jsonify, request
import keyboard
import os
import sys
import webbrowser
import json
import pygetwindow as gw
import time
import psutil
import ctypes
import hmac
from modules.paths import get_config_path
from modules.security import (
    get_or_create_secret,
    get_local_ip,
    verify_socket_payload,
    require_localhost,
    is_localhost,
)

dispatcher_bp = Blueprint("dispatcher", __name__)
CONFIG_FILE = get_config_path("buttons_config.json")

DEFAULT_LAYOUT = {
    "active_layout_id": "profile_main",
    "layouts": [
        {
            "id": "profile_main",
            "name": "Główny Panel",
            "grid": {"columns": 4, "rows": 4},
            "buttons": [
                {
                    "id": "1",
                    "title": "pulpit",
                    "color": "#1a1a1a",
                    "type": "ACTION",
                    "x": 1,
                    "y": 1,
                    "w": 1,
                    "h": 1,
                    "payload": {"command": "hotkey", "args": "win+d"},
                },
                {
                    "id": "2",
                    "title": "task-manager",
                    "color": "#1a1a1a",
                    "type": "ACTION",
                    "x": 2,
                    "y": 1,
                    "w": 1,
                    "h": 1,
                    "payload": {"command": "hotkey", "args": "ctrl+shift+esc"},
                },
                {
                    "id": "5",
                    "title": "pliki",
                    "color": "#1a1a1a",
                    "type": "ACTION",
                    "x": 3,
                    "y": 1,
                    "w": 1,
                    "h": 1,
                    "payload": {"command": "hotkey", "args": "win+e"},
                },
                {
                    "id": "6",
                    "title": "onet",
                    "color": "#1a1a1a",
                    "type": "ACTION",
                    "x": 4,
                    "y": 1,
                    "w": 1,
                    "h": 1,
                    "payload": {
                        "command": "open_url",
                        "args": "https://www.onet.pl/",
                    },
                },
                {
                    "id": "3",
                    "title": "Mixer Audio",
                    "color": "#2ecc71",
                    "type": "WIDGET",
                    "x": 1,
                    "y": 2,
                    "w": 4,
                    "h": 1,
                    "payload": {"command": "open_mixer"},
                },
                {
                    "id": "4",
                    "title": "ram usage",
                    "color": "#5865F2",
                    "type": "LIVE DATA",
                    "x": 1,
                    "y": 3,
                    "w": 2,
                    "h": 2,
                    "payload": {"sensor": "ram"},
                },
                {
                    "id": "7",
                    "title": "prev",
                    "color": "#2ecc71",
                    "type": "ACTION",
                    "x": 3,
                    "y": 3,
                    "w": 1,
                    "h": 1,
                    "payload": {"command": "hotkey", "args": "left arrow"},
                },
                {
                    "id": "8",
                    "title": "next",
                    "color": "#2ecc71",
                    "type": "ACTION",
                    "x": 4,
                    "y": 3,
                    "w": 1,
                    "h": 1,
                    "payload": {"command": "hotkey", "args": "right arrow"},
                },
            ],
        }
    ],
}


def load_default_layout():
    """Ładuje domyślny układ z dołączonego pliku buttons_config.json lub zwraca DEFAULT_LAYOUT."""
    # 1. Sprawdź, czy plik jest spakowany w PyInstaller (sys._MEIPASS)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled_path = os.path.join(sys._MEIPASS, "buttons_config.json")
        if os.path.exists(bundled_path):
            try:
                with open(bundled_path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception:
                pass

    # 2. Sprawdź katalog w repozytorium / obok serwera
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_config = os.path.join(base_dir, "buttons_config.json")
    if os.path.exists(repo_config):
        try:
            with open(repo_config, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            pass

    return DEFAULT_LAYOUT


def execute_command(command, args):
    """Główna funkcja wykonawcza. Eliminuje powtarzanie kodu (DRY)."""
    try:
        if command == "hotkey":
            keyboard.send(args)
            return True, f"Wysłano skrót: {args}"

        elif command == "write":
            keyboard.write(args, exact=True)
            return True, f"Wpisano tekst: {args}"

        elif command == "open_url":
            if isinstance(args, str) and (
                args.startswith("http://") or args.startswith("https://")
            ):
                webbrowser.open(args)
                return True, f"Otwarto stronę: {args}"
            return False, "Niepoprawny URL (dozwolone tylko http:// lub https://)"

        elif command == "workspace":
            if not isinstance(args, list):
                return False, "Niepoprawny format workspace (wymagana lista okien)"

            for target in args:
                title = target.get("title", "")
                exec_path = target.get("exec_path", "")
                matched_windows = gw.getWindowsWithTitle(title)

                if not matched_windows and exec_path:
                    try:
                        os.startfile(exec_path)
                        for _ in range(10):
                            time.sleep(0.5)
                            matched_windows = gw.getWindowsWithTitle(title)
                            if matched_windows:
                                break
                    except Exception as e:
                        print(f"[WARN] Błąd startu {exec_path}: {e}")

                # Przesuwanie i skalowanie
                if matched_windows:
                    win = matched_windows[0]
                    try:
                        if win.isMinimized:
                            win.restore()
                        win.moveTo(target["x"], target["y"])
                        win.resizeTo(target["width"], target["height"])
                        win.activate()
                    except Exception as e:
                        if "Error code from Windows: 0" not in str(e):
                            print(f"[WARN] Błąd przesunięcia okna {title}: {e}")

            return True, "Zastosowano układ Workspace"

        return False, f"Nieznana komenda: {command}"
    except Exception as e:
        return False, str(e)


@dispatcher_bp.route("/get_layout", methods=["GET"])
def get_layout():
    config_file = get_config_path("buttons_config.json")
    try:
        if not os.path.exists(config_file):
            default_data = load_default_layout()
            try:
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=4)
            except Exception as write_err:
                print(f"[WARN] Nie udało się zapisać domyślnego pliku konfiguracji: {write_err}")
            return jsonify(default_data), 200

        with open(config_file, "r", encoding="utf-8-sig") as f:
            layout = json.load(f)
        return jsonify(layout), 200
    except Exception as e:
        print(f"[WARN] Błąd odczytu layoutu: {e}")
        return jsonify(DEFAULT_LAYOUT), 200


@dispatcher_bp.route("/save_layout", methods=["POST"])
@require_localhost
def save_layout():
    try:
        new_layout = request.get_json(silent=True)
        if not isinstance(new_layout, dict) or "layouts" not in new_layout:
            return jsonify({"error": "Niepoprawny format danych układu"}), 400

        config_file = get_config_path("buttons_config.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(new_layout, f, ensure_ascii=False, indent=4)
        return jsonify({"status": "ok", "msg": "Zapisano układ"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dispatcher_bp.route("/scan_windows", methods=["GET"])
@require_localhost
def scan_windows():
    windows = []
    for win in gw.getAllWindows():
        if win.title and win.visible and win.width > 0 and win.height > 0:
            exec_path = ""
            try:
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(
                    win._hWnd, ctypes.byref(pid)
                )
                if pid.value > 0:
                    process = psutil.Process(pid.value)
                    exec_path = process.exe()
            except Exception:
                pass

            windows.append(
                {
                    "title": win.title,
                    "x": win.left,
                    "y": win.top,
                    "width": win.width,
                    "height": win.height,
                    "exec_path": exec_path,
                }
            )
    return jsonify({"status": "ok", "windows": windows})


@dispatcher_bp.route("/get_pairing_data", methods=["GET"])
@require_localhost
def get_pairing_data():
    """Udostępnia dane do kodu QR. Zablokowane tylko dla localhosta!"""
    return jsonify({
        "ip": get_local_ip(),
        "port": 5000,
        "secret": get_or_create_secret()
    })


@dispatcher_bp.route("/trigger", methods=["POST"])
def trigger_action_rest():
    """Bramka dla skryptów zewnętrznych i starego Web Edytora"""
    if not is_localhost(request.remote_addr):
        secret_header = request.headers.get("X-DoDeck-Secret", "")
        expected_secret = get_or_create_secret()
        if not secret_header or not hmac.compare_digest(secret_header, expected_secret):
            return (
                jsonify(
                    {"error": "Brak uprawnień. Wymagany localhost lub poprawny nagłówek X-DoDeck-Secret."}
                ),
                403,
            )

    data = request.get_json(silent=True) or {}
    success, msg = execute_command(data.get("command"), data.get("args", ""))

    if success:
        return jsonify({"status": "ok", "msg": msg})
    return jsonify({"error": msg}), 400


def register_dispatcher_events(socketio):
    """Bramka dla natywnej aplikacji mobilnej (ultra-szybka)"""

    @socketio.on("trigger_action")
    def handle_trigger(data):
        if not verify_socket_payload(data, "action"):
            return

        success, msg = execute_command(
            data.get("command"),
            data.get("args", ""),
        )
        if success:
            print(f"[WS] {msg}")
        else:
            print(f"[WS ERROR] Błąd: {msg}")

    @socketio.on("trigger_macro")
    def handle_macro(data):
        if not verify_socket_payload(data, "macro"):
            return

        steps = data.get("steps", [])
        print(f"[WS] Wykonywanie makra ({len(steps)} kroków)...")

        for step in steps:
            command = step.get("command")
            args = step.get("args", "")
            delay_ms = step.get("delay", 0)

            execute_command(command, args)

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
