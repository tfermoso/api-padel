import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def make_safe_filename(original_filename: str) -> str:
    # Sanitiza y evita path traversal
    safe = secure_filename(original_filename)  # recomendado por Flask/Werkzeug :contentReference[oaicite:4]{index=4}
    ext = safe.rsplit(".", 1)[1].lower() if "." in safe else "bin"
    return f"{uuid.uuid4().hex}.{ext}"

def ensure_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)
