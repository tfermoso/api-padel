import os
from flask import Blueprint, current_app, send_from_directory, abort

media_bp = Blueprint("media", __name__)

@media_bp.get("/<path:filename>")
def get_media(filename):
    folder = current_app.config["UPLOAD_FOLDER"]
    full = os.path.join(folder, filename)
    if not os.path.exists(full):
        abort(404)
    return send_from_directory(folder, filename)
