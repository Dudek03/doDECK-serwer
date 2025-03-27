from flask import Flask, jsonify, request
import subprocess
import keyboard
from flask_cors import CORS  
import psutil
import pygetwindow as gw

app = Flask(__name__)
CORS(app)  # Dodaje wsparcie dla CORS

@app.route('/desktop', methods=['POST'])
def desktop():
    try:
        keyboard.press_and_release('win+d')  # Symulacja naciśnięcia Win + D
        return jsonify({"message": "Win+D pressed: Minimizing all windows"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mute', methods=['POST'])
def mute():
    try:
        subprocess.run(["nircmd.exe", "mutesysvolume", "2"], check=True)  # Użycie nircmd do wyciszenia
        return jsonify({"message": "Toggled mute"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/clip', methods=['POST'])
def clip():
    try:
        keyboard.press_and_release('ctrl+8') 
        return jsonify({"message": "ctrl+8 pressed: Minimizing all windows"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/getApp', methods=['GET'])
def getApps():
    windows = gw.getWindowsWithTitle('')
    active_processes = [window.title for window in windows if window.title]
    print("Procesy na pasku zadań:")
    for title in active_processes:
        print(f"- {title}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)  # Nasłuchuj na wszystkich interfejsach
