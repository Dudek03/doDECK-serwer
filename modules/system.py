from flask import Blueprint, jsonify
import psutil

system_bp = Blueprint("system", __name__)


@system_bp.route("/getCPUUsage", methods=["GET"])
def getCPUUsage():
    try:
        cpuUsage = psutil.cpu_percent(interval=0.1, percpu=True)
        return jsonify({"cpu usage": max(cpuUsage)}), 200
    except Exception as e:
        return jsonify({"error message: ": str(e)}), 500


@system_bp.route("/getRAMUsage", methods=["GET"])
def getRAMUsage():
    try:
        return jsonify({"RAM usage": psutil.virtual_memory().percent}), 200
    except Exception as e:
        return jsonify({"error message: ": str(e)}), 500
