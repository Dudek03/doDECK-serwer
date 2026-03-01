from flask import Blueprint, jsonify
import psutil

system_bp = Blueprint("system", __name__)


@system_bp.route("/getCPUUsage", methods=["GET"])
def getUsageData():
    try:
        cpuUsage = psutil.cpu_percent(interval=0.1, percpu=True)
        ramUsage = psutil.virtual_memory().percent
        return jsonify({"cpu": max(cpuUsage), "ram": ramUsage}), 200
    except Exception as e:
        return jsonify({"error message: ": str(e)}), 500
