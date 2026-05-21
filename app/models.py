from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    estado = db.Column(db.String(50), default='Activo')
    fecha_ingreso = db.Column(db.Date)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(50), default='user')

    inscripciones = db.relationship('InscripcionPostulante', back_populates='usuario')

    def get_id(self):
        return str(self.id_usuario)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Usuario {self.username}>'


class Carrera(db.Model):
    __tablename__ = 'carrera'
    id_carrera = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cod_carrera = db.Column(db.String(50), nullable=False)
    mension = db.Column(db.String(255))
    nombre_carrera = db.Column(db.String(255), nullable=False)

    inscripciones = db.relationship('InscripcionPostulante', back_populates='carrera')

    def __repr__(self):
        return f'<Carrera {self.nombre_carrera}>'


class Estudiante(db.Model):
    __tablename__ = 'estudiante'
    id_Estudiante = db.Column(db.Integer, primary_key=True, autoincrement=True)
    anio_egreso = db.Column(db.Integer)
    celular = db.Column(db.Integer)
    ci = db.Column(db.Integer, nullable=False)
    correo_electronico = db.Column(db.String(255))
    foto = db.Column(db.String(255))
    nombre = db.Column(db.String(255), nullable=False)

    inscripciones = db.relationship('InscripcionPostulante', back_populates='estudiante')

    def __repr__(self):
        return f'<Estudiante {self.nombre}>'


class InscripcionPostulante(db.Model):
    __tablename__ = 'inscripcion_postulante'
    id_inscripcion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estado = db.Column(db.String(50))
    fecha_inscripcion = db.Column(db.Date)
    id_carrera = db.Column(db.Integer, db.ForeignKey('carrera.id_carrera'), nullable=False)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id_Estudiante'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)

    carrera = db.relationship('Carrera', back_populates='inscripciones')
    estudiante = db.relationship('Estudiante', back_populates='inscripciones')
    usuario = db.relationship('Usuario', back_populates='inscripciones')
    pagos = db.relationship('AporizacionDePago', back_populates='inscripcion')

    def __repr__(self):
        return f'<Inscripcion {self.id_inscripcion}>'


class AporizacionDePago(db.Model):
    __tablename__ = 'aporizacion_de_pago'
    id_pago = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_inscripcion = db.Column(db.Integer, db.ForeignKey('inscripcion_postulante.id_inscripcion'), nullable=False)
    fecha_Autorizacion = db.Column(db.Date)
    monto = db.Column(db.Float)

    inscripcion = db.relationship('InscripcionPostulante', back_populates='pagos')

    def __repr__(self):
        return f'<Pago {self.id_pago} - Monto: {self.monto}>'
