from flask import Flask, jsonify, request, send_file
import keyboard
from flask_cors import CORS  
from PIL import Image, ImageOps
import psutil
#import win32gui

app = Flask(__name__)

@app.route("/get-image-binary", methods=["GET"])
def get_image():
    return send_file("example.png", mimetype="image/png")

def changeIconColor(imagePath, color): 
  img = Image.open(f"{imagePath}.png").convert("L")  # Konwersja do skali szarości
  img_colored = ImageOps.colorize(img, black=color, white="white")  # Zmiana czerni na niebieski

  img_colored.save(f"{imagePath}_{color}.png")
  
def giveIconTexture(iconPath, texturePath):
  icon = Image.open(f"{iconPath}.png").convert("L") 
  texture = Image.open(f"{texturePath}.png").convert("RGBA") 

  texture = texture.resize(icon.size)

  result = Image.new("RGBA", icon.size)
  result.paste(texture, (0, 0), mask=icon)

  result.save(f"{iconPath}_{texturePath}.png")
  
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

'''@app.route('/getApp', methods=['GET'])
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
        print(f"{process_name} (PID: {pid}) - {title}")'''

@app.route('/getCPUusage', method=['GET'])
def getCPUUsage():
    print(psutil.cpu_percent())

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
