import json
from contextlib import contextmanager
from flask import Blueprint, jsonify, request
from pycaw.pycaw import (
    AudioUtilities,
    ISimpleAudioVolume,
    IAudioEndpointVolume,
)
import comtypes
from comtypes import CLSCTX_ALL
import win32api
import win32gui

audio_bp = Blueprint("audio", __name__)


@contextmanager
def com_context():
    """Zarządza cyklem życia COM, gwarantując wywołanie CoUninitialize."""
    should_uninit = False
    try:
        comtypes.CoInitialize()
        should_uninit = True
    except Exception:
        should_uninit = False
    try:
        yield
    finally:
        if should_uninit:
            try:
                comtypes.CoUninitialize()
            except Exception:
                pass


@audio_bp.route("/getAppsVolume", methods=["GET"])
def getAudioVolume():
    try:
        apps = []
        with com_context():
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process:
                    try:
                        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                        app_name = session.Process.name()
                        volume_level = volume.GetMasterVolume()
                        muted = volume.GetMute()
                        if muted == 0:
                            apps.append(
                                {
                                    "App": app_name,
                                    "Volume": round(volume_level * 100),
                                    "isMuted": muted,
                                }
                            )
                    except Exception as inner_e:
                        print(f"[WARN] error: {inner_e}")
                        continue
        return jsonify({"ilosc": len(apps), "aplikacje": apps}), 200
    except Exception as outer_e:
        print(f"[ERROR] Główny wyjątek: {outer_e}")
        return jsonify({"error": str(outer_e)}), 500


@audio_bp.route("/setAppVolume", methods=["POST"])
def setAppVolume():
    try:
        data = request.get_json(silent=True) or {}
        app_name = data.get("app")
        volume_value = data.get("volume")

        if not app_name or volume_value is None:
            return jsonify({"error": "Brak wymaganych danych"}), 400

        try:
            volume_value = max(0, min(100, int(round(float(volume_value))))) / 100.0
        except (ValueError, TypeError):
            return jsonify({"error": "Niepoprawna wartość głośności"}), 400

        found = False
        target = str(app_name).lower().strip()

        with com_context():
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                try:
                    if not session.Process:
                        continue
                    proc_name = session.Process.name()
                except Exception:
                    continue

                p_lower = proc_name.lower()
                if (
                    p_lower == target
                    or p_lower.removesuffix(".exe") == target.removesuffix(".exe")
                ):
                    try:
                        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                        volume.SetMasterVolume(volume_value, None)
                        if volume_value > 0:
                            try:
                                if volume.GetMute():
                                    volume.SetMute(0, None)
                            except Exception:
                                pass
                        found = True
                    except Exception as e:
                        print(f"[WARN] Nie udało się ustawić: {e}")
                        continue

        if found:
            return jsonify(
                {"status": "OK", "ustawiona_głośność": int(volume_value * 100)}
            ), 200
        else:
            return jsonify(
                {"error": f"Nie znaleziono aplikacji: {app_name}"},
            ), 404
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@audio_bp.route("/muteAllApps", methods=["GET"])
def muteAllApps():
    try:
        with com_context():
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None,
            )
            volume = interface.QueryInterface(IAudioEndpointVolume)
            mute = volume.GetMute()
            volume.SetMute(bool(not mute), None)
        return jsonify({"status: ": not mute}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@audio_bp.route("/mic3", methods=["GET"])
def mic3():
    try:
        WM_APPCOMMAND = 0x319
        APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000
        hwnd_active = win32gui.GetForegroundWindow()
        win32api.SendMessage(
            hwnd_active, WM_APPCOMMAND, None, APPCOMMAND_MICROPHONE_VOLUME_MUTE
        )
        return jsonify({"status mute: ": "ok"}), 200
    except Exception as e:
        return jsonify({"error: ": str(e)}), 500


def get_session_audio_data(session):
    """Pobiera dane audio dla pojedynczej sesji. Zwraca słownik lub None."""
    if not session.Process:
        return None

    try:
        proc_name = session.Process.name()
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        muted = volume.GetMute()

        if muted != 0:
            return None

        return {
            "App": proc_name,
            "Volume": round(volume.GetMasterVolume() * 100),
            "isMuted": muted,
        }
    except Exception:
        return None


def register_audio_events(socketio):
    @socketio.on("get_audio_volume")
    def handle_get_audio():
        """Zwraca listę aplikacji z ich głośnością przez WebSocket"""
        try:
            apps = []
            with com_context():
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    app_data = get_session_audio_data(session)
                    if app_data:
                        apps.append(app_data)

            socketio.emit(
                "audio_volume_data",
                {
                    "ilosc": len(apps),
                    "aplikacje": apps,
                },
            )
        except Exception as e:
            print(f"[WS] Błąd pobierania audio: {e}")

    @socketio.on("set_audio_volume")
    def handle_set_audio(data):
        """Ustawia głośność danej aplikacji z suwaka"""
        try:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    return

            if not isinstance(data, dict):
                return

            app_name = data.get("app")
            volume_value = data.get("volume")

            if not app_name or volume_value is None:
                return

            try:
                volume_value = max(0, min(100, int(round(float(volume_value))))) / 100.0
            except (ValueError, TypeError):
                return

            target = str(app_name).lower().strip()

            with com_context():
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    try:
                        if not session.Process:
                            continue
                        proc_name = session.Process.name()
                    except Exception:
                        continue

                    p_lower = proc_name.lower()
                    if (
                        p_lower == target
                        or p_lower.removesuffix(".exe") == target.removesuffix(".exe")
                    ):
                        try:
                            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                            volume.SetMasterVolume(volume_value, None)
                            if volume_value > 0:
                                try:
                                    if volume.GetMute():
                                        volume.SetMute(0, None)
                                except Exception:
                                    pass
                        except Exception:
                            continue
        except Exception as e:
            print(f"[WS] Błąd ustawiania głośności: {e}")

    @socketio.on("toggle_mute_all")
    def handle_toggle_mute_all():
        try:
            with com_context():
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_,
                    CLSCTX_ALL,
                    None,
                )
                volume = interface.QueryInterface(IAudioEndpointVolume)
                mute = volume.GetMute()
                volume.SetMute(bool(not mute), None)
            print(f"[WS] Wykonano Mute All: {not mute}")
        except Exception as e:
            print(f"[WS] Błąd wyciszania systemu: {e}")

    @socketio.on("toggle_mic_mute")
    def handle_toggle_mic():
        try:
            WM_APPCOMMAND = 0x319
            APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000
            hwnd_active = win32gui.GetForegroundWindow()
            win32api.SendMessage(
                hwnd_active,
                WM_APPCOMMAND,
                None,
                APPCOMMAND_MICROPHONE_VOLUME_MUTE,
            )
            print("[WS] Wykonano Mute Mikrofonu")
        except Exception as e:
            print(f"[WS] Błąd wyciszania mikrofonu: {e}")
