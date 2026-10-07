from flask import Blueprint, jsonify, request
import keyboard
import os
import webbrowser
import json
import pygetwindow as gw
import subprocess
import time
import psutil
import ctypes

dispatcher_bp = Blueprint("dispatcher", __name__)
CONFIG_FILE = "buttons_config.json"

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
                    "payload": {"command": "open_url", "args": "https://www.onet.pl/"},
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


@dispatcher_bp.route("/get_layout", methods=["GET"])
def get_layout():
    try:
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_LAYOUT, f, ensure_ascii=False, indent=4)
            return jsonify(DEFAULT_LAYOUT), 200

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            layout = json.load(f)
        return jsonify(layout), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dispatcher_bp.route("/save_layout", methods=["POST"])
def save_layout():
    try:
        new_layout = request.get_json()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(new_layout, f, ensure_ascii=False, indent=4)
        return jsonify({"status": "ok", "msg": "Zapisano układ"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dispatcher_bp.route("/scan_windows", methods=["GET"])
def scan_windows():
    """Zwraca listę widocznych okien na ekranie z ich współrzędnymi, wymiarami i ścieżką .exe."""
    windows = []
    for win in gw.getAllWindows():
        if win.title and win.visible and win.width > 0 and win.height > 0:
            exec_path = ""
            try:
                # Magia Windows API: Pobieramy PID z uchwytu okna (win._hWnd)
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(
                    win._hWnd, ctypes.byref(pid)
                )

                if pid.value > 0:
                    process = psutil.Process(pid.value)
                    exec_path = process.exe()
            except Exception:
                # Ignorujemy błędy braku uprawnień
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


@dispatcher_bp.route("/trigger", methods=["POST"])
def trigger_action_rest():
    data = request.get_json()
    command = data.get("command")
    args = data.get("args", "")

    try:
        if command == "hotkey":
            keyboard.send(args)
            return jsonify({"status": "ok", "msg": f"Wysłano: {args}"})
        elif command == "open_url":
            webbrowser.open(args)
            return jsonify({"status": "ok", "msg": "Otwarto stronę"})
        elif command == "workspace":
            for target in args:
                title = target.get("title", "")
                exec_path = target.get("exec_path", "")

                matched_windows = gw.getWindowsWithTitle(title)

                # Jeśli okno nie istnieje, a mamy ścieżkę - odpalamy aplikację
                if not matched_windows and exec_path:
                    try:
                        subprocess.Popen(exec_path)
                        # Czekamy maks 5 sekund (10 * 0.5s) aż okno się pojawi
                        for _ in range(10):
                            time.sleep(0.5)
                            matched_windows = gw.getWindowsWithTitle(title)
                            if matched_windows:
                                break
                    except Exception as e:
                        print(f"[WARN] Nie udało się uruchomić {exec_path}: {e}")

                if matched_windows:
                    win = matched_windows[0]
                    try:
                        if win.isMinimized:
                            win.restore()
                        win.moveTo(target["x"], target["y"])
                        win.resizeTo(target["width"], target["height"])
                        win.activate()
                    except Exception as e:
                        print(f"[WARN] Błąd przesunięcia okna {title}: {e}")
            return jsonify({"status": "ok", "msg": "Zastosowano układ Workspace"})
        else:
            return jsonify({"error": "Nieznana komenda"}), 400
    except Exception as e:
        print(f"[ERROR] Trigger error: {e}")
        return jsonify({"error": str(e)}), 500


def register_dispatcher_events(socketio):
    @socketio.on("trigger_action")
    def handle_trigger(data):
        command = data.get("command")
        args = data.get("args", "")

        try:
            if command == "hotkey":
                keyboard.send(args)
                print(f"🚀 [WS] Wykonano skrót: {args}")
            elif command == "open_url":
                webbrowser.open(args)
                print(f"🌍 [WS] Otwarto stronę: {args}")
            elif command == "workspace":
                for target in args:
                    title = target.get("title", "")
                    exec_path = target.get("exec_path", "")

                    matched_windows = gw.getWindowsWithTitle(title)

                    if not matched_windows and exec_path:
                        try:
                            subprocess.Popen(exec_path)
                            for _ in range(10):
                                time.sleep(0.5)
                                matched_windows = gw.getWindowsWithTitle(title)
                                if matched_windows:
                                    break
                        except Exception as e:
                            print(f"❌ [WS] Błąd startu {exec_path}: {e}")

                    if matched_windows:
                        win = matched_windows[0]
                        try:
                            if win.isMinimized:
                                win.restore()
                            win.moveTo(target["x"], target["y"])
                            win.resizeTo(target["width"], target["height"])
                            win.activate()
                        except Exception as e:
                            print(f"❌ [WS] Błąd przesunięcia okna {title}: {e}")
                print("WS] Zastosowano workspace")
        except Exception as e:
            print(f"❌ [WS] Błąd triggera: {e}")
            print(f"❌ [WS] Błąd triggera: {e}")
