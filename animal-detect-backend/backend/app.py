# app.py
from flask import Flask
from flask_cors import CORS
from backend.routes import routes     # your Blueprint

app = Flask(__name__)

# Register all Blueprints first
app.register_blueprint(routes)

# Then enable CORS globally (fastest to verify things work)
CORS(
    app,
    resources={r"/*": {"origins": "http://172.20.10.2:3000"}},
    supports_credentials=False,          # change to True if you use cookies
    allow_headers=["Content-Type"],      # allow JSON / multipart/form‑data
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
