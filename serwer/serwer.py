from flask import Flask, jsonify, request, send_file
import keyboard
from flask_cors import CORS  
from PIL import Image, ImageOps
import psutil
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import comtypes
#import win32gui

app = Flask(__name__)

def changeIconColor(imagePath, color): 
  img = Image.open(f"{imagePath}.png").convert("L")  
  img_colored = ImageOps.colorize(img, black=color, white="white")  
  img_colored.save(f"{imagePath}_{color}.png")
  
def giveIconTexture(iconPath, texturePath):
  icon = Image.open(f"{iconPath}.png").convert("L") 
  texture = Image.open(f"{texturePath}.png").convert("RGBA") 
  texture = texture.resize(icon.size)
  result = Image.new("RGBA", icon.size)
  result.paste(texture, (0, 0), mask=icon)
  result.save(f"{iconPath}_{texturePath}.png")

@app.route("/get-image-binary", methods=["GET"])
def get_image():
    return send_file("example.png", mimetype="image/png")
  
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

@app.route('/getAppsVolume', methods=['GET'])
def getAudioVolume():
    try:
        comtypes.CoInitialize()
        apps = []
        sessions = AudioUtilities.GetAllSessions()

        for session in sessions:
            if session.Process:
                try:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    app_name = session.Process.name()
                    volume_level = volume.GetMasterVolume()
                    muted = volume.GetMute()
                    if muted == 0:
                        apps.append({
                            "App": app_name,
                            "Volume": round(volume_level * 100),
                            "isMuted": muted
                        })
                except Exception as inner_e:
                    print(f"[WARN] error: {inner_e}")
                    continue

        return jsonify({
            "ilosc": len(apps),
            "aplikacje": apps
        }), 200

    except Exception as outer_e:
        print(f"[ERROR] Główny wyjątek: {outer_e}")
        return jsonify({"error": str(outer_e)}), 500


@app.route('/getCPUusage', methods=['GET'])
def getCPUUsage():
    try:
        cpuUsage = psutil.cpu_percent(interval=1, percpu=True)
        return jsonify({'cpu usage': max(cpuUsage)}), 200
    except Exception as e:
        return jsonify({'error message: ': str(e)}), 500

@app.route('/getRAMusage', methods=['GET'])
def getRAMUsage():
    try:
        return jsonify({'RAM usage': psutil.virtual_memory().percent }), 200
    except Exception as e:
        return jsonify({'error message: ': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
