from modules.dispatcher import register_dispatcher_events
from modules.audio import register_audio_events
from modules.system import register_socket_events
from modules import blueprints
from flask_socketio import SocketIO
from flask_cors import CORS
from flask import Flask, render_template
from PIL import Image, ImageDraw
import webbrowser
import socket
import os
import pystray
import threading

Image.init()


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allower_origins="*")
for bp in blueprints:
    app.register_blueprint(bp, url_prefix=f"/{bp.name}")

register_socket_events(socketio)
register_audio_events(socketio)
register_dispatcher_events(socketio)


@app.route("/")
def index():
    """opens main page of web editor"""
    return render_template("index.html")


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


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


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
