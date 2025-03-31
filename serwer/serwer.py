from flask import Flask, jsonify, request
import subprocess
import keyboard
from flask_cors import CORS  
import psutil
import pygetwindow as gw
import win32gui

app = Flask(__name__)
@app.route('/desktop', methods=['POST'])
def desktop():
    try:
        keyboard.press_and_release('win+d')
        return jsonify({"message": "Win+D pressed: Minimizing all windows"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mute', methods=['POST'])
def mute():
    try:
        keyboard.press_and_release('ctrl+shift+m')
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
def get_active_processes():
    def get_window_pid(hwnd):
        """Zwraca PID procesu dla danego uchwytu okna"""
        _, pid = win32gui.GetWindowThreadProcessId(hwnd)
        return pid

    windows = []
    def enum_window_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd): 
            title = win32gui.GetWindowText(hwnd)
            if title:
                pid = get_window_pid(hwnd)
                windows.append((title, pid))

    win32gui.EnumWindows(enum_window_callback, None)

    processes = {p.pid: p.name() for p in psutil.process_iter(['pid', 'name'])}

    print("Aplikacje na pasku zadań:")
    for title, pid in windows:
        process_name = processes.get(pid, "Unknown")
        print(f"{process_name} (PID: {pid}) - {title}")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
