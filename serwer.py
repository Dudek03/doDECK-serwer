from modules.dispatcher import register_dispatcher_events
from modules.audio import register_audio_events
from modules.system import register_socket_events
from modules.security import get_or_create_secret, get_local_ip, require_localhost
from modules import blueprints
from flask_socketio import SocketIO
from flask_cors import CORS
from flask import Flask, jsonify
from PIL import Image, ImageDraw
import webbrowser
import os
import sys
import pystray
import threading

Image.init()

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

static_dir = os.path.join(BASE_DIR, "web-panel", "dist")
app = Flask(__name__, static_folder=static_dir, static_url_path="/")
CORS(app)
socketio = SocketIO(app, async_mode="gevent", cors_allowed_origins="*")
for bp in blueprints:
    app.register_blueprint(bp, url_prefix=f"/{bp.name}")

register_socket_events(socketio)
register_audio_events(socketio)
register_dispatcher_events(socketio)


@app.route("/")
def index():
    """opens main page of web editor"""
    return app.send_static_file("index.html")


@app.route("/api/pairing")
@require_localhost
def get_pairing_data():
    """Udostępnia dane do kodu QR. Zablokowane tylko dla localhosta!"""
    return jsonify(
        {"ip": get_local_ip(), "port": 5000, "secret": get_or_create_secret()}
    )


def create_default_icon():
    """Generuje prostą zieloną ikonkę z napisem 'dD', jeśli nie masz własnego pliku"""
    image = Image.new("RGB", (64, 64), color=(46, 204, 113))
    d = ImageDraw.Draw(image)
    d.text((15, 25), "dD", fill=(255, 255, 255))
    return image


def quit_application(icon, item):
    """Zamyka aplikację i serwer po kliknięciu 'Zakończ'"""
    icon.stop()
    os._exit(0)


def open_web_editor(icon, item):
    webbrowser.open("http://localhost:5000/")


def setup_tray_icon():
    image = create_default_icon()
    local_ip = get_local_ip()
    menu = pystray.Menu(
        pystray.MenuItem(f"IP: {local_ip}", lambda icon, item: None),
        pystray.MenuItem("Otwórz edytor webowy", open_web_editor),
        pystray.MenuItem("Zakończ doDECK", quit_application),
    )
    icon = pystray.Icon("doDECK", image, f"doDECK ({local_ip})", menu)
    icon.run()


def start_server():
    server_thread = threading.Thread(
        target=lambda: socketio.run(app, host="0.0.0.0", port=5000, use_reloader=False),
        daemon=True,
    )
    server_thread.start()

    setup_tray_icon()


if __name__ == "__main__":
    start_server()
