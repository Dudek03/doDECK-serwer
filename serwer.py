from flask import Flask
from flask_cors import CORS

from modules import blueprints

app = Flask(__name__)
CORS(app)
for bp in blueprints:
    app.register_blueprint(bp, url_prefix=f"/{bp.name}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
