from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS
from pathlib import Path

from .config import Config
from .extensions import db, migrate, jwt

def create_app():
    # raíz del proyecto: .../api-padel
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")  # <-- clave

    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from .auth import auth_bp
    from .api import api_bp
    from .admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route("/")
    def index():
        return {"message": "API Padel funcionando en local!"}

    return app
