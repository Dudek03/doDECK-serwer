from flask import Blueprint, jsonify, request
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, EDataFlow, ERole, IAudioEndpointVolume
import comtypes
from comtypes import CLSCTX_ALL

audio_bp = Blueprint('audio', __name__)

@audio_bp.route('/getAppsVolume', methods = ['GET'])
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

@audio_bp.route('/setAppVolume', methods = ['POST'])
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

@audio_bp.route('/muteAllApps', methods = ['GET'])
def muteAllApps():
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
    