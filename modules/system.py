from flask import Blueprint, jsonify
import psutil

system_bp = Blueprint("system", __name__)
listening_clients = 0


@system_bp.route("/getSystemUsage", methods=["GET"])
def getUsageData():
    try:
        cpuUsage = psutil.cpu_percent(interval=0.1, percpu=True)
        ramUsage = psutil.virtual_memory().percent
        return jsonify({"cpu": max(cpuUsage), "ram": ramUsage}), 200
    except Exception as e:
        return jsonify({"error message: ": str(e)}), 500


def register_socket_events(socketio):
    def telemetry_loop():
        global listening_clients
        while listening_clients > 0:
            cpuUsage = psutil.cpu_percent(interval=0.1, percpu=True)
            ramUsage = psutil.virtual_memory().percent

            socketio.emit("system_update", {"cpu": max(cpuUsage), "ram": ramUsage})
            socketio.sleep(3)

    @socketio.on("subscribe_telemetry")
    def on_subscribe():
        global listening_clients
        listening_clients += 1
        if listening_clients == 1:
            socketio.start_background_task(telemetry_loop)

    @socketio.on("disconnect")
    def on_disconnect():
        global listening_clients
        listening_clients = max(0, listening_clients - 1)
