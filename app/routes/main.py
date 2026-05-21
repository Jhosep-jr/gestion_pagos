from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Usuario, Estudiante, Carrera, InscripcionPostulante, AporizacionDePago

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    total_usuarios = Usuario.query.count()
    total_estudiantes = Estudiante.query.count()
    total_carreras = Carrera.query.count()
    total_inscripciones = InscripcionPostulante.query.count()
    total_pagos = AporizacionDePago.query.count()
    monto_total = sum(p.monto or 0 for p in AporizacionDePago.query.all())
    return render_template('dashboard.html',
                           total_usuarios=total_usuarios,
                           total_estudiantes=total_estudiantes,
                           total_carreras=total_carreras,
                           total_inscripciones=total_inscripciones,
                           total_pagos=total_pagos,
                           monto_total=monto_total)
