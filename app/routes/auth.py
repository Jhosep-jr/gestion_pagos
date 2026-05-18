from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Usuario
from app import db
from werkzeug.security import generate_password_hash
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Bienvenido, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/usuarios')
@login_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios)


@auth_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_usuario():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        rol = request.form.get('rol', 'user')
        estado = request.form.get('estado', 'Activo')
        fecha_str = request.form.get('fecha_ingreso')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
        else:
            u = Usuario(username=username, email=email,
                        password_hash=generate_password_hash(password),
                        rol=rol, estado=estado, fecha_ingreso=fecha)
            db.session.add(u)
            db.session.commit()
            flash('Usuario creado correctamente.', 'success')
            return redirect(url_for('auth.listar_usuarios'))
    return render_template('auth/form_usuario.html', usuario=None)


@auth_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    u = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        u.username = request.form.get('username')
        u.email = request.form.get('email')
        u.rol = request.form.get('rol', 'user')
        u.estado = request.form.get('estado', 'Activo')
        fecha_str = request.form.get('fecha_ingreso')
        u.fecha_ingreso = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        new_pass = request.form.get('password')
        if new_pass:
            u.set_password(new_pass)
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('auth.listar_usuarios'))
    return render_template('auth/form_usuario.html', usuario=u)


@auth_bp.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_usuario(id):
    u = Usuario.query.get_or_404(id)
    db.session.delete(u)
    db.session.commit()
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('auth.listar_usuarios'))
