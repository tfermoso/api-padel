from flask import Flask, request
from dotenv import load_dotenv
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate, jwt

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)  # útil para React luego

    db.init_app(app)
    migrate.init_app(app, db)  # migraciones via Flask-Migrate :contentReference[oaicite:6]{index=6}
    jwt.init_app(app)
    
    from .auth import auth_bp
    from .api import api_bp
    from .admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    
    @app.route("/")
    def index():
        return {"message": "API Padel funcionando!"}
    
  

    return app
