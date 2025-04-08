from flask import Flask, jsonify, request, send_file
import keyboard
from flask_cors import CORS  
from PIL import Image, ImageOps
import psutil
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, EDataFlow, ERole, IAudioEndpointVolume
import comtypes
#from pycaw.utils import AudioUtilities as UtilsAudio
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL

import win32api
import win32gui



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

@app.route('/setAppVolume', methods=['POST'])
def setAppVolume():
    try:
        comtypes.CoInitialize()
        data = request.get_json()
        app_name = data.get("app")
        volume_value = data.get("volume")

        if not app_name or volume_value is None:
            return jsonify({"error": "Brak wymaganych danych"}), 400

        # Konwersja 0–100 → 0.0–1.0
        volume_value = max(0, min(100, int(volume_value))) / 100.0

        sessions = AudioUtilities.GetAllSessions()
        found = False

        for session in sessions:
            if session.Process and session.Process.name().lower() == app_name.lower():
                try:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    volume.SetMasterVolume(volume_value, None)
                    found = True
                except Exception as e:
                    print(f"[WARN] Nie udało się ustawić: {e}")
                    continue

        if found:
            return jsonify({"status": "OK", "ustawiona_głośność": int(volume_value * 100)}), 200
        else:
            return jsonify({"error": f"Nie znaleziono aplikacji: {app_name}"}), 404

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/muteAll', methods=['GET'])
def setMicMute():
    try:
        comtypes.CoInitialize()
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)

        mute = volume.GetMute()

        volume.SetMute(bool(not mute), None)

        return jsonify({"status: ": not mute}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/setMicMute', methods=['GET'])
def setMic():
    try:
        comtypes.CoInitialize()

        devices = AudioUtilities.GetAllDevices()

        capture_devices = []
        for device in devices:
            try:
                if device.DataFlow == EDataFlow.eCapture:
                    capture_devices.append(device)
            except AttributeError:
                # Jeśli nie ma tego atrybutu, po prostu pomijamy
                continue

        if not capture_devices:
            return jsonify({"error": "Nie znaleziono aktywnego mikrofonu", "lista: ": devices}), 404

        # Wybierz pierwsze urządzenie nagrywające
        mic = capture_devices[0]

        # Aktywuj urządzenie i pobierz interfejs głośności
        interface = mic.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Pobierz dane z żądania JSON
        data = request.get_json()
        mute = data.get("mute")

        if mute is None:
            return jsonify({"error": "Brak pola 'mute' (true/false)"}), 400

        # Wycisz lub przywróć mikrofon
        volume.SetMute(bool(mute), None)

        return jsonify({
            "status": "OK",
            "mikrofon": "wyciszony" if mute else "odciszony"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/mic3', methods=['GET'])
def mic3():

    try:
        WM_APPCOMMAND = 0x319
        APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000

        hwnd_active = win32gui.GetForegroundWindow()
        win32api.SendMessage(hwnd_active, WM_APPCOMMAND, None, APPCOMMAND_MICROPHONE_VOLUME_MUTE)
        return jsonify({"status mute: ": "ok"}), 200
    except Exception as e:
        return jsonify({"error: ": str(e)}), 500

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
