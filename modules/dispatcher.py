from flask import Blueprint, jsonify, request
import keyboard
import os
import webbrowser
import json

dispatcher_bp = Blueprint("dispatcher", __name__)
CONFIG_FILE = "buttons_config.json"

DEFAULT_LAYOUT = [
    {
        "id": "1",
        "title": "Pulpit",
        "color": "#1a1a1a",
        "type": "ACTION",
        "payload": {"command": "hotkey", "args": "win+d"},
    },
    {
        "id": "2",
        "title": "Mixer Audio",
        "color": "#2ecc71",
        "type": "WIDGET",
        "payload": {"command": "open_mixer"},
    },
    {
        "id": "3",
        "title": "ram usage",
        "color": "#5865F2",
        "type": "LIVE DATA",
        "payload": {"sensor": "ram"},
    },
    {
        "id": "4",
        "title": "pliki",
        "color": "#1a1a1a",
        "type": "ACTION",
        "payload": {"command": "hotkey", "args": "win+e"},
    },
    {
        "id": "5",
        "title": "onet",
        "color": "#1a1a1a",
        "type": "ACTION",
        "payload": {"command": "open_url", "args": "https://www.onet.pl/"},
    },
]


@dispatcher_bp.route("/get_layout", methods=["GET"])
def get_layout():
    try:
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump(DEFAULT_LAYOUT, f)
            return jsonify(DEFAULT_LAYOUT), 200

        with open(CONFIG_FILE, "r") as f:
            layout = json.load(f)
        return jsonify(layout), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dispatcher_bp.route("/save_layout", methods=["POST"])
def save_layout():
    try:
        new_layout = request.get_json()
        with open(CONFIG_FILE, "w") as f:
            json.dump(new_layout, f)
        return jsonify({"status": "ok", "msg": "Zapisano układ"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dispatcher_bp.route("/trigger", methods=["POST"])
def trigger_action():
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

        # TODO

        else:
            return jsonify({"error": "Nieznana komenda"}), 400

    except Exception as e:
        print(f"[ERROR] Trigger error: {e}")
        return jsonify({"error": str(e)}), 500
