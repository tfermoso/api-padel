import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # .../api-padel
INSTANCE_DIR = BASE_DIR / "instance"                      # .../api-padel/instance
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)           # opcional: asegura que exista

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt")

    db_url = os.getenv("DATABASE_URL", "sqlite:///padel.db")

    # sqlite relativa: sqlite:///padel.db  -> usar .../instance/padel.db
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        filename = db_url[len("sqlite:///"):]             # "padel.db"
        db_path = (INSTANCE_DIR / filename).resolve()
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path.as_posix()
    else:
        SQLALCHEMY_DATABASE_URI = db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "10")) * 1024 * 1024
