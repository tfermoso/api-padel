from datetime import datetime
from .extensions import db
from sqlalchemy import (
    CheckConstraint,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import relationship
class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)

    # Relaciones
    usuarios = relationship("Usuario", back_populates="rol", cascade="all,delete", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Rol {self.id} {self.nombre}>"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    dni = db.Column(db.String(20), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)  # almacenar HASH, no texto plano
    foto = db.Column(db.String(500), nullable=True)

    rol_id = db.Column(
        db.Integer,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    reservas = relationship("Reserva", back_populates="usuario", cascade="all,delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Usuario {self.id} {self.email}>"


class Pista(db.Model):
    __tablename__ = "pistas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    cubierta = db.Column(db.Boolean, nullable=False, default=False)
    plazas = db.Column(db.Integer, nullable=False)
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("plazas > 0", name="ck_pistas_plazas_gt_0"),
        CheckConstraint("precio_base >= 0", name="ck_pistas_precio_base_ge_0"),
    )

    # Relaciones
    reservas = relationship("Reserva", back_populates="pista", cascade="all,delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Pista {self.id} {self.nombre}>"


class Horario(db.Model):
    __tablename__ = "horarios"

    id = db.Column(db.Integer, primary_key=True)
    franja = db.Column(db.String(50), nullable=False)  # ej: "09:00-10:30"
    turno = db.Column(db.String(50), nullable=False)   # ej: "mañana", "tarde", "noche"

    __table_args__ = (
        UniqueConstraint("franja", "turno", name="uq_horarios_franja_turno"),
    )

    # Relaciones
    horarios_reserva = relationship(
        "HorarioReserva",
        back_populates="horario",
        cascade="all,delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Horario {self.id} {self.franja} {self.turno}>"


class Extra(db.Model):
    __tablename__ = "extras"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    precio_extra = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("precio_extra >= 0", name="ck_extras_precio_extra_ge_0"),
    )

    def __repr__(self) -> str:
        return f"<Extra {self.id} {self.nombre}>"


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    pista_id = db.Column(
        db.Integer,
        ForeignKey("pistas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fecha = db.Column(db.Date, nullable=False, index=True)

    # Relaciones
    usuario = relationship("Usuario", back_populates="reservas")
    pista = relationship("Pista", back_populates="reservas")

    horarios = relationship(
        "HorarioReserva",
        back_populates="reserva",
        cascade="all,delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Reserva {self.id} user={self.usuario_id} pista={self.pista_id} fecha={self.fecha}>"


class HorarioReserva(db.Model):
    __tablename__ = "horarios_reserva"

    id = db.Column(db.Integer, primary_key=True)

    reserva_id = db.Column(
        db.Integer,
        ForeignKey("reservas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    horario_id = db.Column(
        db.Integer,
        ForeignKey("horarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    precio = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("precio >= 0", name="ck_horarios_reserva_precio_ge_0"),
        # Evita duplicar el mismo horario dentro de la misma reserva
        UniqueConstraint("reserva_id", "horario_id", name="uq_horarios_reserva_reserva_horario"),
    )

    # Relaciones
    reserva = relationship("Reserva", back_populates="horarios")
    horario = relationship("Horario", back_populates="horarios_reserva")

    def __repr__(self) -> str:
        return f"<HorarioReserva {self.id} reserva={self.reserva_id} horario={self.horario_id} precio={self.precio}>"
