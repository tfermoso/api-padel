from flask import Blueprint, request,current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .utils import allowed_file, make_safe_filename, ensure_folder

from .extensions import db
from .models import Usuario as User
import os
auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    nombre = (data.get("nombre") or "").strip().lower()
    dni = (data.get("dni") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password or not nombre or not dni:
        return {"error": "todos los campos son obligatorios"}, 400

    if User.query.filter_by(email=email).first():
        return {"error": "email ya existe"}, 409
    user = User(
            name=nombre,
            email=email,
            password_hash=generate_password_hash(password),
            rol_id=1,
            dni=dni
        )
    db.session.add(user)
    db.session.commit()
    return {"id": user.id, "email": user.email, "nombre": user.nombre, "dni": user.dni, "rol_id": user.rol_id}, 201

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return {"error": "credenciales inválidas"}, 401

    # identity como string para JWT
    token = create_access_token(identity=str(user.id))  # :contentReference[oaicite:7]{index=7}
    return {"access_token": token,"user":user.nombre,"rol": user.rol.nombre}, 200

@auth_bp.post("/delete")
def delete_account():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    #borrar usuario de la base de datos
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return {"message": "cuenta eliminada"}, 200

@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return {"id": user.id, "email": user.email, "nombre": user.nombre, "dni": user.dni, "foto": user.foto,"rol_id": user.rol_id,"rol": user.rol.nombre}, 200

@auth_bp.post("/change_password")
@jwt_required() 
def change_password():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""

    user = User.query.get_or_404(user_id)

    if not check_password_hash(user.password, old_password):
        return {"error": "contraseña antigua incorrecta"}, 401

    user.password = generate_password_hash(new_password)
    db.session.commit()
    return {"message": "contraseña actualizada"}, 200

@auth_bp.post("/update_image_profile")
@jwt_required()
def update_image_profile(): 
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    # Debug: verificar qué se envía
    if "foto" not in request.files:
        return {"error": "no se ha enviado ninguna imagen en 'foto'", "keys_recibidas": list(request.files.keys())}, 400

    file = request.files["foto"]
    
    # Debug completo
    print(f"DEBUG: file = {file}")
    print(f"DEBUG: file.filename = {file.filename}")
    print(f"DEBUG: bool(file) = {bool(file)}")
    print(f"DEBUG: hasattr filename = {hasattr(file, 'filename')}")
    
    filename = file.filename.strip() if file.filename else ""
    
    if not filename or filename == "":
        return {"error": "filename vacío", "filename_recibido": f"'{file.filename}'", "tipo_file": str(type(file))}, 400

    if not allowed_file(filename):
        return {"error": "tipo de archivo no permitido", "archivo": filename}, 400

    try:
        safe_filename = make_safe_filename(filename)
        ensure_folder(current_app.config["UPLOAD_FOLDER"])
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_filename)
        file.save(filepath)

        user.foto = safe_filename
        db.session.commit()

        return {"message": "imagen de perfil actualizada", "foto": safe_filename}, 200
    
    except Exception as e:
        db.session.rollback()
        return {"error": "error al guardar la imagen", "detail": str(e)}, 500