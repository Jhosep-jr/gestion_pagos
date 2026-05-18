from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models import Carrera
from app import db

carrera_bp = Blueprint('carrera', __name__, url_prefix='/carrera')


@carrera_bp.route('/')
@login_required
def listar():
    carreras = Carrera.query.all()
    return render_template('carrera/listar.html', carreras=carreras)


@carrera_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        c = Carrera(
            cod_carrera=request.form.get('cod_carrera'),
            mension=request.form.get('mension'),
            nombre_carrera=request.form.get('nombre_carrera')
        )
        db.session.add(c)
        db.session.commit()
        flash('Carrera registrada correctamente.', 'success')
        return redirect(url_for('carrera.listar'))
    return render_template('carrera/form.html', c=None)


@carrera_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    c = Carrera.query.get_or_404(id)
    if request.method == 'POST':
        c.cod_carrera = request.form.get('cod_carrera')
        c.mension = request.form.get('mension')
        c.nombre_carrera = request.form.get('nombre_carrera')
        db.session.commit()
        flash('Carrera actualizada.', 'success')
        return redirect(url_for('carrera.listar'))
    return render_template('carrera/form.html', c=c)


@carrera_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    c = Carrera.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash('Carrera eliminada.', 'success')
    return redirect(url_for('carrera.listar'))
