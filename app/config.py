import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # .../api-padel

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt")

    db_url = os.getenv("DATABASE_URL", "sqlite:///padel.db")

    # si es sqlite relativa: sqlite:///padel.db -> sqlite:////home/.../api-padel/padel.db
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        filename = db_url.replace("sqlite:///", "", 1)
        db_path = (BASE_DIR / filename).resolve()
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path.as_posix()}"
    else:
        SQLALCHEMY_DATABASE_URI = db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "10")) * 1024 * 1024
