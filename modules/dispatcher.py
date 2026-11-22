from typing import Tuple, Dict, Any, List, Optional
from flask import Blueprint, jsonify, request, Response
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
CONFIG_FILE: str = get_config_path("buttons_config.json")

DEFAULT_LAYOUT: Dict[str, Any] = {
    "active_layout_id": "profile_main",
    "layouts": [
        {
            "id": "profile_main",
            "name": "Main Panel",
            "grid": {"columns": 4, "rows": 4},
            "buttons": [
                {
                    "id": "1",
                    "title": "desktop",
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
                    "title": "explorer",
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
                    "title": "browser",
                    "color": "#1a1a1a",
                    "type": "ACTION",
                    "x": 4,
                    "y": 1,
                    "w": 1,
                    "h": 1,
                    "payload": {
                        "command": "open_url",
                        "args": "https://www.google.com/",
                    },
                },
                {
                    "id": "3",
                    "title": "Audio Mixer",
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


def load_default_layout() -> Dict[str, Any]:
    """Loads default layout from bundled buttons_config.json or returns DEFAULT_LAYOUT."""
    # 1. Check if packaged in PyInstaller (sys._MEIPASS)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled_path = os.path.join(sys._MEIPASS, "buttons_config.json")
        if os.path.exists(bundled_path):
            try:
                with open(bundled_path, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception:
                pass

    # 2. Check repo / server root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_config = os.path.join(base_dir, "buttons_config.json")
    if os.path.exists(repo_config):
        try:
            with open(repo_config, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            pass

    return DEFAULT_LAYOUT


def execute_command(command: Optional[str], args: Any) -> Tuple[bool, str]:
    """Executes dispatcher commands (hotkey, write, open_url, workspace)."""
    try:
        if command == "hotkey":
            keyboard.send(args)
            return True, f"Hotkey sent: {args}"

        elif command == "write":
            keyboard.write(args, exact=True)
            return True, f"Text written: {args}"

        elif command == "open_url":
            if isinstance(args, str) and (
                args.startswith("http://") or args.startswith("https://")
            ):
                webbrowser.open(args)
                return True, f"URL opened: {args}"
            return False, "Invalid URL (only http:// or https:// allowed)"

        elif command == "workspace":
            if not isinstance(args, list):
                return False, "Invalid workspace format (list of windows required)"

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
                        print(f"[WARN] Error launching {exec_path}: {e}")

                # Move and resize window
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
                            print(f"[WARN] Error moving window {title}: {e}")

            return True, "Workspace layout applied"

        return False, f"Unknown command: {command}"
    except Exception as e:
        return False, str(e)


@dispatcher_bp.route("/get_layout", methods=["GET"])
def get_layout() -> Tuple[Response, int]:
    config_file = get_config_path("buttons_config.json")
    try:
        if not os.path.exists(config_file):
            default_data = load_default_layout()
            try:
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=4)
            except Exception as write_err:
                print(f"[WARN] Failed to save default config file: {write_err}")
            return jsonify(default_data), 200

        with open(config_file, "r", encoding="utf-8-sig") as f:
            layout = json.load(f)
        return jsonify(layout), 200
    except Exception as e:
        print(f"[WARN] Error reading layout: {e}")
        return jsonify(DEFAULT_LAYOUT), 200


@dispatcher_bp.route("/save_layout", methods=["POST"])
@require_localhost
def save_layout() -> Tuple[Response, int]:
    try:
        new_layout = request.get_json(silent=True)
        if not isinstance(new_layout, dict) or "layouts" not in new_layout:
            return jsonify({"error": "Invalid layout data format"}), 400

        config_file = get_config_path("buttons_config.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(new_layout, f, ensure_ascii=False, indent=4)
        return jsonify({"status": "ok", "msg": "Layout saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dispatcher_bp.route("/scan_windows", methods=["GET"])
@require_localhost
def scan_windows() -> Tuple[Response, int]:
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
    return jsonify({"status": "ok", "windows": windows}), 200


@dispatcher_bp.route("/get_pairing_data", methods=["GET"])
@require_localhost
def get_pairing_data() -> Tuple[Response, int]:
    """Provides pairing data for QR code. Restricted to localhost."""
    return jsonify({
        "ip": get_local_ip(),
        "port": 5000,
        "secret": get_or_create_secret()
    }), 200


@dispatcher_bp.route("/trigger", methods=["POST"])
def trigger_action_rest() -> Tuple[Response, int]:
    """Gateway for external scripts and REST clients."""
    if not is_localhost(request.remote_addr):
        secret_header = request.headers.get("X-DoDeck-Secret", "")
        expected_secret = get_or_create_secret()
        if not secret_header or not hmac.compare_digest(secret_header, expected_secret):
            return (
                jsonify(
                    {"error": "Unauthorized. Localhost or valid X-DoDeck-Secret header required."}
                ),
                403,
            )

    data = request.get_json(silent=True) or {}
    success, msg = execute_command(data.get("command"), data.get("args", ""))

    if success:
        return jsonify({"status": "ok", "msg": msg}), 200
    return jsonify({"error": msg}), 400


def register_dispatcher_events(socketio: Any) -> None:
    """Socket.IO gateway for native mobile app."""

    @socketio.on("trigger_action")
    def handle_trigger(data: Any) -> Any:
        if not verify_socket_payload(data, "action"):
            return {"status": "error", "msg": "Invalid HMAC or timestamp"}

        success, msg = execute_command(
            data.get("command"),
            data.get("args", ""),
        )
        if success:
            print(f"[WS] {msg}")
            return {"status": "ok", "msg": msg}
        else:
            print(f"[WS ERROR] Error: {msg}")
            return {"status": "error", "msg": msg}

    @socketio.on("trigger_macro")
    def handle_macro(data: Any) -> None:
        if not verify_socket_payload(data, "macro"):
            return

        steps = data.get("steps", [])
        print(f"[WS] Executing macro ({len(steps)} steps)...")

        for step in steps:
            command = step.get("command")
            args = step.get("args", "")
            delay_ms = step.get("delay", 0)

            execute_command(command, args)

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
