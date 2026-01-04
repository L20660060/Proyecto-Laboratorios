from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'alumno' o 'consulta'
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True)  # matrícula para alumnos

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    estado = db.Column(db.String(20), default='Disponible')
    condicion = db.Column(db.Text)
    multa_por_dia = db.Column(db.Float, default=50.0)  # <-- NUEVO CAMPO: precio de multa por día

class Prestamo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo.id'), nullable=False)
    alumno_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha_prestamo = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_devolucion = db.Column(db.DateTime)
    fecha_prevista_devolucion = db.Column(db.DateTime)  # fecha límite
    estado = db.Column(db.String(20), default='Activo')
    
    # Nuevos campos para multa
    dias_retraso = db.Column(db.Integer, default=0)
    multa_aplicada = db.Column(db.Float, default=0.0)  # monto total de la multa

    equipo = db.relationship('Equipo', backref='prestamos')
    alumno = db.relationship('User', backref='prestamos')