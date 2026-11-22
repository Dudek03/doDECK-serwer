from typing import Tuple
from flask import Blueprint, jsonify, Response
from flask_socketio import SocketIO
import psutil

system_bp = Blueprint("system", __name__)
listening_clients: int = 0


@system_bp.route("/getSystemUsage", methods=["GET"])
def getUsageData() -> Tuple[Response, int]:
    try:
        cpuUsage = psutil.cpu_percent(interval=0.1, percpu=True)
        ramUsage = psutil.virtual_memory().percent
        return jsonify({"cpu": max(cpuUsage), "ram": ramUsage}), 200
    except Exception as e:
        return jsonify({"error": str(e), "error message: ": str(e)}), 500


def register_socket_events(socketio: SocketIO) -> None:
    def telemetry_loop() -> None:
        global listening_clients
        while listening_clients > 0:
            cpuUsage = psutil.cpu_percent(interval=0.1, percpu=True)
            ramUsage = psutil.virtual_memory().percent

            socketio.emit(
                "system_update",
                {
                    "cpu": max(cpuUsage),
                    "ram": ramUsage,
                },
            )
            socketio.sleep(3)

    @socketio.on("subscribe_telemetry")
    def on_subscribe() -> None:
        global listening_clients
        listening_clients += 1
        if listening_clients == 1:
            socketio.start_background_task(telemetry_loop)

    @socketio.on("disconnect")
    def on_disconnect() -> None:
        global listening_clients
        listening_clients = max(0, listening_clients - 1)
