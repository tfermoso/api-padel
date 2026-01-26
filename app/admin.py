from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import Usuario, Pista, Horario, Extra, Reserva, Rol
from .utils import allowed_file, make_safe_filename, ensure_folder
import os
from flask import current_app

admin_bp = Blueprint("admin", __name__)


def _user_id() -> int:
    return int(get_jwt_identity())


def _check_admin():
    """Verifica que el usuario autenticado sea administrador (rol nombre 'admin')"""
    user_id = _user_id()
    user = db.session.get(Usuario, user_id)
    
    if not user or user.rol.nombre != "admin":
        return False, {"error": "acceso denegado: requiere rol de administrador"}, 403
    
    return True, None, None


# ==================== USUARIOS ====================

@admin_bp.get("/usuarios")
@jwt_required()
def get_usuarios():
    """Obtener lista de todos los usuarios"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    usuarios = Usuario.query.all()
    result = []
    
    for usuario in usuarios:
        result.append({
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "dni": usuario.dni,
            "foto": usuario.foto,
            "rol_id": usuario.rol_id,
            "rol_nombre": usuario.rol.nombre if usuario.rol else None,
        })
    
    return {"usuarios": result}, 200


@admin_bp.get("/usuarios/<int:usuario_id>")
@jwt_required()
def get_usuario(usuario_id):
    """Obtener detalles de un usuario específico"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return {"error": "usuario no encontrado"}, 404
    
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "dni": usuario.dni,
        "foto": usuario.foto,
        "rol_id": usuario.rol_id,
        "rol_nombre": usuario.rol.nombre if usuario.rol else None,
    }, 200


@admin_bp.put("/usuarios/<int:usuario_id>")
@jwt_required()
def update_usuario(usuario_id):
    """Actualizar datos de un usuario"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return {"error": "usuario no encontrado"}, 404
    
    data = request.get_json(silent=True) or {}
    
    if "nombre" in data:
        usuario.nombre = data["nombre"].strip()
    
    if "email" in data:
        email = data["email"].strip().lower()
        # Verificar que el email no exista en otro usuario
        existing = Usuario.query.filter_by(email=email).first()
        if existing and existing.id != usuario_id:
            return {"error": "email ya existe"}, 409
        usuario.email = email
    
    if "dni" in data:
        dni = data["dni"].strip()
        # Verificar que el DNI no exista en otro usuario
        existing = Usuario.query.filter_by(dni=dni).first()
        if existing and existing.id != usuario_id:
            return {"error": "dni ya existe"}, 409
        usuario.dni = dni
    
    if "rol_id" in data:
        rol_id = data["rol_id"]
        rol = db.session.get(Rol, rol_id)
        if not rol:
            return {"error": "rol no encontrado"}, 404
        usuario.rol_id = rol_id
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error de integridad al actualizar usuario"}, 400
    
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "dni": usuario.dni,
        "rol_id": usuario.rol_id,
    }, 200


@admin_bp.delete("/usuarios/<int:usuario_id>")
@jwt_required()
def delete_usuario(usuario_id):
    """Eliminar un usuario"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    # No permitir que un administrador se elimine a sí mismo
    current_user_id = _user_id()
    if usuario_id == current_user_id:
        return {"error": "no puedes eliminarte a ti mismo"}, 400
    
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return {"error": "usuario no encontrado"}, 404
    
    try:
        db.session.delete(usuario)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al eliminar usuario"}, 400
    
    return {"message": "usuario eliminado correctamente"}, 200


# ==================== PISTAS ====================

@admin_bp.post("/pistas")
@jwt_required()
def crear_pista():
    """Crear una nueva pista"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    data = request.get_json(silent=True) or {}
    
    nombre = (data.get("nombre") or "").strip()
    cubierta = data.get("cubierta", False)
    plazas = data.get("plazas")
    precio_base = data.get("precio_base")
    
    if not nombre or plazas is None or precio_base is None:
        return {"error": "nombre, plazas y precio_base son obligatorios"}, 400
    
    try:
        plazas = int(plazas)
        precio_base = float(precio_base)
    except (TypeError, ValueError):
        return {"error": "plazas debe ser entero y precio_base debe ser número"}, 400
    
    if plazas <= 0:
        return {"error": "plazas debe ser mayor a 0"}, 400
    
    if precio_base < 0:
        return {"error": "precio_base no puede ser negativo"}, 400
    
    # Verificar nombre único
    if Pista.query.filter_by(nombre=nombre).first():
        return {"error": "nombre de pista ya existe"}, 409
    
    try:
        pista = Pista(
            nombre=nombre,
            cubierta=cubierta,
            plazas=plazas,
            precio_base=precio_base
        )
        db.session.add(pista)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al crear pista"}, 400
    
    return {
        "id": pista.id,
        "nombre": pista.nombre,
        "cubierta": pista.cubierta,
        "plazas": pista.plazas,
        "precio_base": str(pista.precio_base),
    }, 201


@admin_bp.put("/pistas/<int:pista_id>")
@jwt_required()
def update_pista(pista_id):
    """Actualizar una pista existente"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    pista = db.session.get(Pista, pista_id)
    if not pista:
        return {"error": "pista no encontrada"}, 404
    
    data = request.get_json(silent=True) or {}
    
    if "nombre" in data:
        nombre = data["nombre"].strip()
        # Verificar que el nombre no exista en otra pista
        existing = Pista.query.filter_by(nombre=nombre).first()
        if existing and existing.id != pista_id:
            return {"error": "nombre de pista ya existe"}, 409
        pista.nombre = nombre
    
    if "cubierta" in data:
        pista.cubierta = bool(data["cubierta"])
    
    if "plazas" in data:
        try:
            plazas = int(data["plazas"])
            if plazas <= 0:
                return {"error": "plazas debe ser mayor a 0"}, 400
            pista.plazas = plazas
        except (TypeError, ValueError):
            return {"error": "plazas debe ser entero"}, 400
    
    if "precio_base" in data:
        try:
            precio_base = float(data["precio_base"])
            if precio_base < 0:
                return {"error": "precio_base no puede ser negativo"}, 400
            pista.precio_base = precio_base
        except (TypeError, ValueError):
            return {"error": "precio_base debe ser número"}, 400
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al actualizar pista"}, 400
    
    return {
        "id": pista.id,
        "nombre": pista.nombre,
        "cubierta": pista.cubierta,
        "plazas": pista.plazas,
        "precio_base": str(pista.precio_base),
    }, 200


@admin_bp.delete("/pistas/<int:pista_id>")
@jwt_required()
def delete_pista(pista_id):
    """Eliminar una pista"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    pista = db.session.get(Pista, pista_id)
    if not pista:
        return {"error": "pista no encontrada"}, 404
    
    try:
        db.session.delete(pista)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al eliminar pista"}, 400
    
    return {"message": "pista eliminada correctamente"}, 200


# ==================== HORARIOS ====================

@admin_bp.post("/horarios")
@jwt_required()
def crear_horario():
    """Crear un nuevo horario"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    data = request.get_json(silent=True) or {}
    
    franja = (data.get("franja") or "").strip()
    turno = (data.get("turno") or "").strip()
    
    if not franja or not turno:
        return {"error": "franja y turno son obligatorios"}, 400
    
    # Verificar que no exista el mismo horario
    existing = Horario.query.filter_by(franja=franja, turno=turno).first()
    if existing:
        return {"error": "horario ya existe"}, 409
    
    try:
        horario = Horario(franja=franja, turno=turno)
        db.session.add(horario)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al crear horario"}, 400
    
    return {
        "id": horario.id,
        "franja": horario.franja,
        "turno": horario.turno,
    }, 201


@admin_bp.put("/horarios/<int:horario_id>")
@jwt_required()
def update_horario(horario_id):
    """Actualizar un horario existente"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return {"error": "horario no encontrado"}, 404
    
    data = request.get_json(silent=True) or {}
    
    if "franja" in data:
        franja = data["franja"].strip()
        # Verificar que no exista otro horario con la misma franja y turno
        turno = horario.turno
        if "turno" in data:
            turno = data["turno"].strip()
        
        existing = Horario.query.filter_by(franja=franja, turno=turno).first()
        if existing and existing.id != horario_id:
            return {"error": "horario ya existe"}, 409
        horario.franja = franja
    
    if "turno" in data:
        turno = data["turno"].strip()
        franja = horario.franja
        if "franja" in data:
            franja = data["franja"].strip()
        
        existing = Horario.query.filter_by(franja=franja, turno=turno).first()
        if existing and existing.id != horario_id:
            return {"error": "horario ya existe"}, 409
        horario.turno = turno
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al actualizar horario"}, 400
    
    return {
        "id": horario.id,
        "franja": horario.franja,
        "turno": horario.turno,
    }, 200


@admin_bp.delete("/horarios/<int:horario_id>")
@jwt_required()
def delete_horario(horario_id):
    """Eliminar un horario"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return {"error": "horario no encontrado"}, 404
    
    try:
        db.session.delete(horario)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al eliminar horario"}, 400
    
    return {"message": "horario eliminado correctamente"}, 200


# ==================== EXTRAS ====================

@admin_bp.post("/extras")
@jwt_required()
def crear_extra():
    """Crear un nuevo extra"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    data = request.get_json(silent=True) or {}
    
    nombre = (data.get("nombre") or "").strip()
    precio_extra = data.get("precio_extra")
    
    if not nombre or precio_extra is None:
        return {"error": "nombre y precio_extra son obligatorios"}, 400
    
    try:
        precio_extra = float(precio_extra)
    except (TypeError, ValueError):
        return {"error": "precio_extra debe ser número"}, 400
    
    if precio_extra < 0:
        return {"error": "precio_extra no puede ser negativo"}, 400
    
    # Verificar nombre único
    if Extra.query.filter_by(nombre=nombre).first():
        return {"error": "nombre de extra ya existe"}, 409
    
    try:
        extra = Extra(nombre=nombre, precio_extra=precio_extra)
        db.session.add(extra)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al crear extra"}, 400
    
    return {
        "id": extra.id,
        "nombre": extra.nombre,
        "precio_extra": str(extra.precio_extra),
    }, 201


@admin_bp.put("/extras/<int:extra_id>")
@jwt_required()
def update_extra(extra_id):
    """Actualizar un extra existente"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    extra = db.session.get(Extra, extra_id)
    if not extra:
        return {"error": "extra no encontrado"}, 404
    
    data = request.get_json(silent=True) or {}
    
    if "nombre" in data:
        nombre = data["nombre"].strip()
        # Verificar que el nombre no exista en otro extra
        existing = Extra.query.filter_by(nombre=nombre).first()
        if existing and existing.id != extra_id:
            return {"error": "nombre de extra ya existe"}, 409
        extra.nombre = nombre
    
    if "precio_extra" in data:
        try:
            precio_extra = float(data["precio_extra"])
            if precio_extra < 0:
                return {"error": "precio_extra no puede ser negativo"}, 400
            extra.precio_extra = precio_extra
        except (TypeError, ValueError):
            return {"error": "precio_extra debe ser número"}, 400
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al actualizar extra"}, 400
    
    return {
        "id": extra.id,
        "nombre": extra.nombre,
        "precio_extra": str(extra.precio_extra),
    }, 200


@admin_bp.delete("/extras/<int:extra_id>")
@jwt_required()
def delete_extra(extra_id):
    """Eliminar un extra"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    extra = db.session.get(Extra, extra_id)
    if not extra:
        return {"error": "extra no encontrado"}, 404
    
    try:
        db.session.delete(extra)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al eliminar extra"}, 400
    
    return {"message": "extra eliminado correctamente"}, 200


# ==================== RESERVAS ====================

@admin_bp.get("/reservas")
@jwt_required()
def get_todas_reservas():
    """Obtener todas las reservas (solo para administradores)"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    reservas = Reserva.query.all()
    result = []
    
    for reserva in reservas:
        horarios = []
        total = 0
        
        for hr in reserva.horarios:
            h = hr.horario
            precio = float(hr.precio)
            total += precio
            
            horarios.append({
                "horario_reserva_id": hr.id,
                "horario_id": h.id,
                "franja": h.franja,
                "turno": h.turno,
                "precio": f"{precio:.2f}",
            })
        
        total_precio = getattr(reserva, "total_precio", total)
        
        result.append({
            "id": reserva.id,
            "usuario_id": reserva.usuario_id,
            "usuario_email": reserva.usuario.email if reserva.usuario else None,
            "usuario_nombre": reserva.usuario.nombre if reserva.usuario else None,
            "pista_id": reserva.pista_id,
            "pista_nombre": reserva.pista.nombre if reserva.pista else None,
            "fecha": reserva.fecha.strftime("%Y-%m-%d") if reserva.fecha else None,
            "total_precio": f"{total_precio:.2f}",
            "horarios": horarios,
        })
    
    return {"reservas": result}, 200


@admin_bp.get("/reservas/<int:reserva_id>")
@jwt_required()
def get_reserva_detalle(reserva_id):
    """Obtener detalles de una reserva específica"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        return {"error": "reserva no encontrada"}, 404
    
    horarios = []
    total = 0
    
    for hr in reserva.horarios:
        h = hr.horario
        precio = float(hr.precio)
        total += precio
        
        horarios.append({
            "horario_reserva_id": hr.id,
            "horario_id": h.id,
            "franja": h.franja,
            "turno": h.turno,
            "precio": f"{precio:.2f}",
        })
    
    total_precio = getattr(reserva, "total_precio", total)
    
    return {
        "id": reserva.id,
        "usuario_id": reserva.usuario_id,
        "usuario_email": reserva.usuario.email if reserva.usuario else None,
        "usuario_nombre": reserva.usuario.nombre if reserva.usuario else None,
        "pista_id": reserva.pista_id,
        "pista_nombre": reserva.pista.nombre if reserva.pista else None,
        "fecha": reserva.fecha.strftime("%Y-%m-%d") if reserva.fecha else None,
        "total_precio": f"{total_precio:.2f}",
        "horarios": horarios,
    }, 200


@admin_bp.delete("/reservas/<int:reserva_id>")
@jwt_required()
def delete_reserva_admin(reserva_id):
    """Eliminar una reserva (solo administrador)"""
    is_admin, error_response, status_code = _check_admin()
    if not is_admin:
        return error_response, status_code
    
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        return {"error": "reserva no encontrada"}, 404
    
    try:
        db.session.delete(reserva)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "error al eliminar reserva"}, 400
    
    return {"message": "reserva eliminada correctamente"}, 200
