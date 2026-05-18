import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app.models import Estudiante
from app import db
from werkzeug.utils import secure_filename

estudiante_bp = Blueprint('estudiante', __name__, url_prefix='/estudiante')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@estudiante_bp.route('/')
@login_required
def listar():
    estudiantes = Estudiante.query.all()
    return render_template('estudiante/listar.html', estudiantes=estudiantes)


@estudiante_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        foto_filename = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Nombre único para evitar colisiones
                import time
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                foto_filename = filename

        e = Estudiante(
            anio_egreso=request.form.get('anio_egreso') or None,
            celular=request.form.get('celular') or None,
            ci=request.form.get('ci'),
            correo_electronico=request.form.get('correo_electronico'),
            foto=foto_filename,
            nombre=request.form.get('nombre')
        )
        db.session.add(e)
        db.session.commit()
        flash('Estudiante registrado correctamente.', 'success')
        return redirect(url_for('estudiante.listar'))
    return render_template('estudiante/form.html', e=None)


@estudiante_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    e = Estudiante.query.get_or_404(id)
    if request.method == 'POST':
        e.anio_egreso = request.form.get('anio_egreso') or None
        e.celular = request.form.get('celular') or None
        e.ci = request.form.get('ci')
        e.correo_electronico = request.form.get('correo_electronico')
        e.nombre = request.form.get('nombre')

        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename and allowed_file(file.filename):
                # Borrar foto anterior
                if e.foto:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], e.foto)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                import time
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                e.foto = filename

        db.session.commit()
        flash('Estudiante actualizado.', 'success')
        return redirect(url_for('estudiante.listar'))
    return render_template('estudiante/form.html', e=e)


@estudiante_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    e = Estudiante.query.get_or_404(id)
    if e.foto:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], e.foto)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(e)
    db.session.commit()
    flash('Estudiante eliminado.', 'success')
    return redirect(url_for('estudiante.listar'))
