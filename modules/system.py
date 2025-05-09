from flask import Blueprint, jsonify
import psutil
import keyboard

system_bp = Blueprint('system', __name__)

@system_bp.route('/getCPUUsage', methods = ['GET'])
def getCPUUsage():
    try:
        cpuUsage = psutil.cpu_percent(interval=1, percpu=True)
        return jsonify({'cpu usage': max(cpuUsage)}), 200
    except Exception as e:
        return jsonify({'error message: ': str(e)}), 500

@system_bp.route('/getRAMUsage', methods = ['GET'])
def getRAMUsage():
    try:
        return jsonify({'RAM usage': psutil.virtual_memory().percent }), 200
    except Exception as e:
        return jsonify({'error message: ': str(e)}), 500

@system_bp.route('/handleDesktop', methods = ['GET'])
def desktop():
    try:
        keyboard.press_and_release('win+d')
        return jsonify({"message": "Win+D pressed: Minimizing all windows"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@system_bp.route('/handleClip', methods = ['GET'])
def clip():
    try:
        keyboard.press_and_release('ctrl+8') 
        return jsonify({"message": "ctrl+8 pressed: Minimizing all windows"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500