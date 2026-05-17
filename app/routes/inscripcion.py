from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models import InscripcionPostulante, Carrera, Estudiante, Usuario
from app import db
from datetime import datetime

inscripcion_bp = Blueprint('inscripcion', __name__, url_prefix='/inscripcion')


@inscripcion_bp.route('/')
@login_required
def listar():
    inscripciones = InscripcionPostulante.query.all()
    return render_template('inscripcion/listar.html', inscripciones=inscripciones)


@inscripcion_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    carreras = Carrera.query.all()
    estudiantes = Estudiante.query.all()
    usuarios = Usuario.query.all()
    if request.method == 'POST':
        fecha_str = request.form.get('fecha_inscripcion')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        insc = InscripcionPostulante(
            estado=request.form.get('estado'),
            fecha_inscripcion=fecha,
            id_carrera=request.form.get('id_carrera'),
            id_estudiante=request.form.get('id_estudiante'),
            id_usuario=request.form.get('id_usuario')
        )
        db.session.add(insc)
        db.session.commit()
        flash('Inscripción registrada correctamente.', 'success')
        return redirect(url_for('inscripcion.listar'))
    return render_template('inscripcion/form.html', insc=None,
                           carreras=carreras, estudiantes=estudiantes, usuarios=usuarios)


@inscripcion_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    insc = InscripcionPostulante.query.get_or_404(id)
    carreras = Carrera.query.all()
    estudiantes = Estudiante.query.all()
    usuarios = Usuario.query.all()
    if request.method == 'POST':
        insc.estado = request.form.get('estado')
        fecha_str = request.form.get('fecha_inscripcion')
        insc.fecha_inscripcion = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        insc.id_carrera = request.form.get('id_carrera')
        insc.id_estudiante = request.form.get('id_estudiante')
        insc.id_usuario = request.form.get('id_usuario')
        db.session.commit()
        flash('Inscripción actualizada.', 'success')
        return redirect(url_for('inscripcion.listar'))
    return render_template('inscripcion/form.html', insc=insc,
                           carreras=carreras, estudiantes=estudiantes, usuarios=usuarios)


@inscripcion_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    insc = InscripcionPostulante.query.get_or_404(id)
    db.session.delete(insc)
    db.session.commit()
    flash('Inscripción eliminada.', 'success')
    return redirect(url_for('inscripcion.listar'))
