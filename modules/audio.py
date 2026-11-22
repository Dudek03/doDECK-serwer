import json
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple, Union
from flask import Blueprint, jsonify, request, Response
from flask_socketio import SocketIO
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
def com_context() -> Generator[None, None, None]:
    """Manages COM lifecycle, ensuring CoUninitialize is called."""
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
def getAudioVolume() -> Tuple[Response, int]:
    try:
        apps: List[Dict[str, Any]] = []
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
                        print(f"[WARN] Error reading session: {inner_e}")
                        continue
        return jsonify({
            "count": len(apps),
            "apps": apps,
            "ilosc": len(apps),
            "aplikacje": apps,
        }), 200
    except Exception as outer_e:
        print(f"[ERROR] Main audio exception: {outer_e}")
        return jsonify({"error": str(outer_e)}), 500


@audio_bp.route("/setAppVolume", methods=["POST"])
def setAppVolume() -> Tuple[Response, int]:
    try:
        data = request.get_json(silent=True) or {}
        app_name = data.get("app")
        volume_value = data.get("volume")

        if not app_name or volume_value is None:
            return jsonify({"error": "Missing required data"}), 400

        try:
            parsed_volume: float = max(0, min(100, int(round(float(volume_value))))) / 100.0
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid volume value"}), 400

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
                        volume.SetMasterVolume(parsed_volume, None)
                        if parsed_volume > 0:
                            try:
                                if volume.GetMute():
                                    volume.SetMute(0, None)
                            except Exception:
                                pass
                        found = True
                    except Exception as e:
                        print(f"[WARN] Failed to set volume: {e}")
                        continue

        if found:
            return jsonify(
                {
                    "status": "OK",
                    "set_volume": int(parsed_volume * 100),
                    "ustawiona_głośność": int(parsed_volume * 100),
                }
            ), 200
        else:
            return jsonify(
                {"error": f"Application not found: {app_name}"},
            ), 404
    except Exception as e:
        print(f"[ERROR] setAppVolume error: {e}")
        return jsonify({"error": str(e)}), 500


@audio_bp.route("/muteAllApps", methods=["GET"])
def muteAllApps() -> Tuple[Response, int]:
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
def mic3() -> Tuple[Response, int]:
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


def get_session_audio_data(session: Any) -> Optional[Dict[str, Any]]:
    """Retrieves audio data for a single session. Returns dict or None."""
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


def register_audio_events(socketio: SocketIO) -> None:
    @socketio.on("get_audio_volume")
    def handle_get_audio() -> None:
        """Returns list of applications with their volume levels via WebSocket."""
        try:
            apps: List[Dict[str, Any]] = []
            with com_context():
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    app_data = get_session_audio_data(session)
                    if app_data:
                        apps.append(app_data)

            socketio.emit(
                "audio_volume_data",
                {
                    "count": len(apps),
                    "apps": apps,
                    "ilosc": len(apps),
                    "aplikacje": apps,
                },
            )
        except Exception as e:
            print(f"[WS] Error fetching audio: {e}")

    @socketio.on("set_audio_volume")
    def handle_set_audio(data: Union[str, Dict[str, Any]]) -> None:
        """Sets the volume of a given application from a slider."""
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
                parsed_volume: float = max(0, min(100, int(round(float(volume_value))))) / 100.0
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
                            volume.SetMasterVolume(parsed_volume, None)
                            if parsed_volume > 0:
                                try:
                                    if volume.GetMute():
                                        volume.SetMute(0, None)
                                except Exception:
                                    pass
                        except Exception:
                            continue
        except Exception as e:
            print(f"[WS] Error setting volume: {e}")

    @socketio.on("toggle_mute_all")
    def handle_toggle_mute_all() -> None:
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
            print(f"[WS] Mute All executed: {not mute}")
        except Exception as e:
            print(f"[WS] Error muting system audio: {e}")

    @socketio.on("toggle_mic_mute")
    def handle_toggle_mic() -> None:
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
            print("[WS] Mic Mute executed")
        except Exception as e:
            print(f"[WS] Error muting microphone: {e}")
