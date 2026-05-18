import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'gestion_pagos_secret_2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345678@localhost/gestion_de_pagos'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Carpeta de uploads
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder.'
    login_manager.login_message_category = 'warning'

    from app.models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.estudiante import estudiante_bp
    from app.routes.carrera import carrera_bp
    from app.routes.inscripcion import inscripcion_bp
    from app.routes.pago import pago_bp
    from app.routes.reportes import reportes_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(estudiante_bp)
    app.register_blueprint(carrera_bp)
    app.register_blueprint(inscripcion_bp)
    app.register_blueprint(pago_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        _seed_default_user()

    return app


def _seed_default_user():
    from app.models import Usuario
    from werkzeug.security import generate_password_hash
    from datetime import date
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(
            username='admin',
            email='admin@gestionpagos.com',
            password_hash=generate_password_hash('admin123'),
            rol='admin',
            estado='Activo',
            fecha_ingreso=date.today()
        )
        db.session.add(admin)
        db.session.commit()
