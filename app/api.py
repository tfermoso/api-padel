import os
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Usuario, Pista, Horario, Extra, Reserva, HorarioReserva
from .utils import allowed_file, make_safe_filename, ensure_folder

api_bp = Blueprint("api", __name__)


def _user_id() -> int:
    return int(get_jwt_identity())


@api_bp.get("/pistas")
@jwt_required()
def get_pistas():
    pistas = Pista.query.all()
    result = []
    for pista in pistas:
        result.append({
            "id": pista.id,
            "nombre": pista.nombre,
            "cubierta": pista.cubierta,
            "precio_base": str(pista.precio_base),
            "plazas": getattr(pista, "plazas", None),
        })
    return {"pistas": result}, 200


@api_bp.get("/horarios")
@jwt_required()
def get_horarios():
    horarios = Horario.query.all()
    result = []
    for horario in horarios:
        result.append({
            "id": horario.id,
            "franja": horario.franja,
            "turno": horario.turno,
        })
    return {"horarios": result}, 200


@api_bp.post("/disponibilidadpista")
@jwt_required()
def get_disponibilidades():
    data = request.get_json(silent=True) or {}

    pista_id = data.get("pista_id")
    fecha = data.get("fecha")

    if pista_id is None or not fecha:
        return {"error": "pista_id y fecha son obligatorios"}, 400

    try:
        pista_id = int(pista_id)
    except (TypeError, ValueError):
        return {"error": "pista_id debe ser entero"}, 400

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "fecha debe tener formato YYYY-MM-DD"}, 400

    todos_horarios = Horario.query.all()

    reservados = (
        db.session.query(Horario.id)
        .join(HorarioReserva, HorarioReserva.horario_id == Horario.id)
        .join(Reserva, Reserva.id == HorarioReserva.reserva_id)
        .filter(Reserva.pista_id == pista_id, Reserva.fecha == fecha_dt)
        .all()
    )
    reservados_ids = {r[0] for r in reservados}

    disponibles = [
        {"id": h.id, "franja": h.franja, "turno": h.turno}
        for h in todos_horarios
        if h.id not in reservados_ids
    ]

    return {"disponibilidades": disponibles}, 200


@api_bp.post("/disponibilidad")
@jwt_required()
def get_disponibilidades_todas_pistas_post():
    data = request.get_json(silent=True) or {}
    fecha = data.get("fecha")

    if not fecha:
        return {"error": "fecha es obligatoria"}, 400

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "fecha debe tener formato YYYY-MM-DD"}, 400

    pistas = Pista.query.all()
    horarios = Horario.query.all()

    reservados = (
        db.session.query(Reserva.pista_id, HorarioReserva.horario_id)
        .join(HorarioReserva, HorarioReserva.reserva_id == Reserva.id)
        .filter(Reserva.fecha == fecha_dt)
        .all()
    )

    reservados_por_pista = {}
    for pista_id, horario_id in reservados:
        reservados_por_pista.setdefault(pista_id, set()).add(horario_id)

    result = []
    for pista in pistas:
        reservados_ids = reservados_por_pista.get(pista.id, set())

        disponibles = [
            {"id": h.id, "franja": h.franja, "turno": h.turno}
            for h in horarios
            if h.id not in reservados_ids
        ]

        result.append({
            "pista_id": pista.id,
            "pista_nombre": pista.nombre,
            "disponibilidades": disponibles
        })

    return {"disponibilidades_por_pista": result}, 200


@api_bp.post("/calcular_precio")
@jwt_required()
def calcular_precio():
    data = request.get_json(silent=True) or {}
    pista_id = data.get("pista_id")
    fecha = data.get("fecha")
    horario_ids = data.get("horario_ids", [])

    if pista_id is None or not fecha or not horario_ids:
        return {"error": "pista_id, fecha y horario_ids son obligatorios"}, 400

    try:
        pista_id = int(pista_id)
    except (TypeError, ValueError):
        return {"error": "pista_id debe ser entero"}, 400

    try:
        horario_ids = [int(h) for h in horario_ids]
    except (TypeError, ValueError):
        return {"error": "horario_ids debe contener ids enteros"}, 400

    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "fecha debe tener formato YYYY-MM-DD"}, 400

    pista = db.session.get(Pista, pista_id)
    if not pista:
        return {"error": "pista no encontrada"}, 404

    # Validar horarios
    count_horarios = Horario.query.filter(Horario.id.in_(horario_ids)).count()
    if count_horarios != len(set(horario_ids)):
        return {"error": "algún horario no existe"}, 400

    precio_franja = Decimal(str(pista.precio_base))
    total_precio = precio_franja * Decimal(len(set(horario_ids)))

    # Extra fin de semana (una vez)
    es_fin_semana = (fecha_dt.weekday() >= 5)
    extra_aplicado = None
    if es_fin_semana:
        extra = Extra.query.filter(db.func.lower(Extra.nombre) == "fin de semana").first()
        if extra:
            extra_importe = Decimal(str(extra.precio_extra))
            total_precio += extra_importe
            extra_aplicado = {
                "id": extra.id,
                "nombre": extra.nombre,
                "precio_extra": f"{extra_importe:.2f}"
            }

    return {
        "total_precio": f"{total_precio:.2f}",
        "precio_por_franja": f"{precio_franja:.2f}",
        "extra_aplicado": extra_aplicado
    }, 200


@api_bp.get("/mis_reservas")
@jwt_required()
def get_mis_reservas():
    user_id = _user_id()
    reservas = Reserva.query.filter_by(usuario_id=user_id).all()

    result = []
    for reserva in reservas:
        horarios = []
        total = Decimal("0.00")

        for hr in reserva.horarios:  # relación Reserva.horarios -> HorarioReserva
            h = hr.horario          # relación HorarioReserva.horario -> Horario
            precio = Decimal(str(hr.precio))
            total += precio

            horarios.append({
                "horario_reserva_id": hr.id,
                "horario_id": h.id,
                "franja": h.franja,
                "turno": h.turno,
                "precio": f"{precio:.2f}",
            })

        # Si tu Reserva guarda total_precio, úsalo; si no, calcula
        total_precio = getattr(reserva, "total_precio", None)
        if total_precio is None:
            total_precio = total

        result.append({
            "id": reserva.id,
            "pista_id": reserva.pista_id,
            "pista_nombre": reserva.pista.nombre if reserva.pista else None,
            "fecha": reserva.fecha.strftime("%Y-%m-%d") if reserva.fecha else None,
            "total_precio": f"{Decimal(str(total_precio)):.2f}",
            "horarios": horarios,
        })

    return {"reservas": result}, 200


@api_bp.post("/reservar")
@jwt_required()
def reservar():
    user_id = _user_id()

    data = request.get_json(silent=True) or {}
    pista_id = data.get("pista_id")
    fecha_str = data.get("fecha")
    horario_ids = data.get("horario_ids", [])

    if pista_id is None or not fecha_str or not horario_ids:
        return {"error": "pista_id, fecha y horario_ids son obligatorios"}, 400

    try:
        pista_id = int(pista_id)
    except (TypeError, ValueError):
        return {"error": "pista_id debe ser entero"}, 400

    if not isinstance(horario_ids, list) or len(horario_ids) == 0:
        return {"error": "horario_ids debe ser una lista no vacía"}, 400

    try:
        horario_ids = [int(h) for h in horario_ids]
    except (TypeError, ValueError):
        return {"error": "horario_ids debe contener ids enteros"}, 400

    # Eliminar duplicados manteniendo orden
    horario_ids = list(dict.fromkeys(horario_ids))

    try:
        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "fecha debe tener formato YYYY-MM-DD"}, 400

    pista = db.session.get(Pista, pista_id)
    if not pista:
        return {"error": "pista no encontrada"}, 404

    horarios = Horario.query.filter(Horario.id.in_(horario_ids)).all()
    if len(horarios) != len(horario_ids):
        existentes = {h.id for h in horarios}
        faltan = sorted(list(set(horario_ids) - existentes))
        return {"error": "algunos horarios no existen", "horarios_inexistentes": faltan}, 400

    conflictos = (
        db.session.query(HorarioReserva.horario_id)
        .join(Reserva, Reserva.id == HorarioReserva.reserva_id)
        .filter(
            Reserva.pista_id == pista_id,
            Reserva.fecha == fecha_dt,
            HorarioReserva.horario_id.in_(horario_ids)
        )
        .all()
    )
    if conflictos:
        ocupados = sorted([c[0] for c in conflictos])
        return {
            "error": "hay horarios no disponibles",
            "pista_id": pista_id,
            "fecha": fecha_str,
            "horarios_ocupados": ocupados
        }, 409

    precio_franja = Decimal(str(pista.precio_base))
    total_precio = precio_franja * Decimal(len(horario_ids))

    extra_aplicado = None
    es_fin_semana = (fecha_dt.weekday() >= 5)
    if es_fin_semana:
        extra = Extra.query.filter(db.func.lower(Extra.nombre) == "fin de semana").first()
        if extra:
            extra_importe = Decimal(str(extra.precio_extra))
            total_precio += extra_importe
            extra_aplicado = {
                "id": extra.id,
                "nombre": extra.nombre,
                "precio_extra": f"{extra_importe:.2f}"
            }

    try:
        reserva = Reserva(
            usuario_id=user_id,
            pista_id=pista_id,
            fecha=fecha_dt
        )

        if hasattr(Reserva, "total_precio"):
            reserva.total_precio = total_precio

        db.session.add(reserva)
        db.session.flush()  # reserva.id

        for hid in horario_ids:
            db.session.add(HorarioReserva(
                reserva_id=reserva.id,
                horario_id=hid,
                precio=precio_franja
            ))

        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return {"error": "conflicto al crear reserva (posible doble reserva)"}, 409

    except Exception as e:
        db.session.rollback()
        return {"error": "error interno creando la reserva", "detail": str(e)}, 500

    # Respuesta detallada
    horarios_map = {h.id: h for h in horarios}
    detalle_horarios = []
    for hid in sorted(horario_ids):
        h = horarios_map[hid]
        detalle_horarios.append({
            "horario_id": h.id,
            "franja": h.franja,
            "turno": h.turno,
            "precio": f"{precio_franja:.2f}"
        })

    return {
        "reserva": {
            "id": reserva.id,
            "usuario_id": user_id,
            "pista": {"id": pista.id, "nombre": pista.nombre},
            "fecha": fecha_str,
            "total_precio": f"{total_precio:.2f}",
            "extra_aplicado": extra_aplicado,
            "horarios": detalle_horarios
        }
    }, 201


@api_bp.post("/cancelar_reserva")
@jwt_required()
def cancelar_reserva():
    user_id = _user_id()
    data = request.get_json(silent=True) or {}
    reserva_id = data.get("reserva_id")

    if reserva_id is None:
        return {"error": "reserva_id es obligatorio"}, 400

    try:
        reserva_id = int(reserva_id)
    except (TypeError, ValueError):
        return {"error": "reserva_id debe ser entero"}, 400

    reserva = db.session.get(Reserva, reserva_id)
    if not reserva or reserva.usuario_id != user_id:
        return {"error": "reserva no encontrada o no autorizada"}, 404

    # Eliminar horarios asociados (ORM: delete-orphan sería mejor, pero mantenemos tu enfoque)
    HorarioReserva.query.filter_by(reserva_id=reserva.id).delete()
    db.session.delete(reserva)
    db.session.commit()

    return {"message": "reserva cancelada"}, 200
