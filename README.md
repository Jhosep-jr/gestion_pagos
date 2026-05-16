# 🎓 Sistema de Gestión de Pagos - Flask

Sistema web académico desarrollado con **Python + Flask + SQLAlchemy**.

## 👥 Integrantes del Equipo
- Integrante 1 (rama: `feature/personal-estudiante`)
- Integrante 2 (rama: `feature/inscripcion-pagos`)
- Integrante 3 (rama: `feature/reportes-graficas`) *(opcional)*

## 🗃️ Base de Datos
`gestion_de_pagos` — 5 tablas con relaciones:

| Tabla | Descripción |
|---|---|
| `usuario` | Autenticación del sistema |
| `personal` | Personal administrativo |
| `estudiante` | Estudiantes postulantes |
| `carrera` | Carreras disponibles |
| `inscripcion_postulante` | Inscripciones (relaciona Estudiante + Carrera + Personal) |
| `aporizacion_de_pago` | Pagos autorizados por inscripción |

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/gestion_pagos.git
cd gestion_pagos

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python run.py
```

Abrir en navegador: http://127.0.0.1:5000

**Credenciales por defecto:**
- Usuario: `admin`
- Contraseña: `admin123`

## 🔗 Módulos del Sistema

| Módulo | URL | Descripción |
|---|---|---|
| Dashboard | `/` | Resumen general con estadísticas |
| Personal | `/personal/` | CRUD de personal administrativo |
| Estudiantes | `/estudiante/` | CRUD de estudiantes |
| Carreras | `/carrera/` | CRUD de carreras |
| Inscripciones | `/inscripcion/` | CRUD de inscripciones |
| Pagos | `/pago/` | CRUD de pagos autorizados |
| Reportes | `/reportes/` | Reportes con 3 gráficas dinámicas |
| Usuarios | `/auth/usuarios` | CRUD de usuarios del sistema |

## 📊 Reportes y Gráficas
- **Gráfica de Barras**: Monto total recaudado por carrera
- **Gráfica de Pastel**: Distribución de inscripciones por estado
- **Gráfica de Línea**: Evolución de pagos mensuales

## 🌿 Flujo de Trabajo GitHub

```bash
# Cada integrante trabaja en su rama
git checkout -b feature/mi-modulo

# Commits frecuentes
git add .
git commit -m "feat: agregar CRUD de estudiantes"
git push origin feature/mi-modulo

# Merge a main cuando esté listo
git checkout main
git merge feature/mi-modulo
```

## 🧱 Estructura del Proyecto

```
gestion_pagos/
├── run.py                   # Punto de entrada
├── requirements.txt         # Dependencias
├── app/
│   ├── __init__.py          # Factory de la app + Login Manager
│   ├── models.py            # Modelos SQLAlchemy con relaciones
│   ├── routes/
│   │   ├── auth.py          # Login, Logout, Usuarios
│   │   ├── main.py          # Dashboard
│   │   ├── personal.py      # CRUD Personal
│   │   ├── estudiante.py    # CRUD Estudiante
│   │   ├── carrera.py       # CRUD Carrera
│   │   ├── inscripcion.py   # CRUD Inscripción
│   │   ├── pago.py          # CRUD Pagos
│   │   └── reportes.py      # Reportes + API JSON gráficas
│   └── templates/
│       ├── base.html        # Layout principal con sidebar
│       ├── dashboard.html
│       ├── auth/            # Login, Usuarios
│       ├── personal/        # Listar + Form
│       ├── estudiante/      # Listar + Form
│       ├── carrera/         # Listar + Form
│       ├── inscripcion/     # Listar + Form
│       ├── pago/            # Listar + Form
│       └── reportes/        # Reportes con gráficas Chart.js
```

## 🛠️ Tecnologías
- **Backend**: Python 3.x, Flask 3.0, SQLAlchemy 2.0
- **Autenticación**: Flask-Login
- **Base de Datos**: SQLite (desarrollo)
- **Frontend**: Bootstrap 5, Chart.js 4, Font Awesome 6
- **Control de versiones**: GitHub (branches por integrante)
