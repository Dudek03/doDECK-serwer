from flask import Blueprint, jsonify
import keyboard

discord_bp = Blueprint('discord', __name__)

@discord_bp.route('/muteDiscord', methods = ['GET'])
def mute():
    try:
        keyboard.press_and_release('ctrl+shift+m')
        return jsonify({"message": "Toggled mute"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500