from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app                  # si create_app está en app/__init__.py
from app.extensions import db
from app.models import Pista, Horario, Extra,Rol 


def get_turno(hh_mm: str) -> str:
    h = int(hh_mm.split(":")[0])
    if 8 <= h < 14:
        return "mañana"
    if 14 <= h < 20:
        return "tarde"
    return "noche"


def seed_pistas():
    pistas = [
        {"nombre": "Pista 1", "cubierta": False, "plazas": 4, "precio_base": Decimal("12.00")},
        {"nombre": "Pista 2", "cubierta": False, "plazas": 4, "precio_base": Decimal("12.00")},
        {"nombre": "Pista 3", "cubierta": True,  "plazas": 4, "precio_base": Decimal("12.00")},
        {"nombre": "Pista 4", "cubierta": True,  "plazas": 4, "precio_base": Decimal("12.00")},
        {"nombre": "Pista 5", "cubierta": False, "plazas": 4, "precio_base": Decimal("12.00")},
        {"nombre": "Pista 6", "cubierta": False, "plazas": 4, "precio_base": Decimal("12.00")},
        {"nombre": "Pista 7", "cubierta": True,  "plazas": 4, "precio_base": Decimal("12.00")},
        {"nombre": "Pista 8", "cubierta": True,  "plazas": 2, "precio_base": Decimal("6.00")},
    ]
    for p in pistas:
        if not Pista.query.filter_by(nombre=p["nombre"]).first():
            db.session.add(Pista(**p))


def seed_horarios():
    start = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("23:00", "%H:%M")

    t = start
    while t < end:
        t2 = t + timedelta(minutes=30)
        franja = f"{t.strftime('%H:%M')}-{t2.strftime('%H:%M')}"
        turno = get_turno(t.strftime("%H:%M"))

        if not Horario.query.filter_by(franja=franja, turno=turno).first():
            db.session.add(Horario(franja=franja, turno=turno))

        t = t2


def seed_extras():
    if not Extra.query.filter_by(nombre="Fin de semana").first():
        db.session.add(Extra(nombre="Fin de semana", precio_extra=Decimal("3.00")))

def seed_roles():
    if not Rol.query.filter_by(nombre="admin").first():
        db.session.add(Rol(nombre="admin"))
    if not Rol.query.filter_by(nombre="usuario").first():
        db.session.add(Rol(nombre="usuario"))


def main():
    app = create_app()
    with app.app_context():
        seed_pistas()
        seed_horarios()
        seed_extras()
        seed_roles()
        db.session.commit()
        print("OK: datos iniciales cargados.")


if __name__ == "__main__":
    main()