import json
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.models import AporizacionDePago, InscripcionPostulante, Carrera, Estudiante, Usuario
from app import db
from sqlalchemy import func
import requests
import os

import requests
from dotenv import load_dotenv

reportes_ia_bp = Blueprint('reportes_ia', __name__, url_prefix='/reportes-ia')

# ─────────────────────────────────────────────
# Función central: llama a la API de Anthropic
# ─────────────────────────────────────────────
base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, '.env')) # Intenta cargarlo de la carpeta actual
load_dotenv(os.path.join(base_dir, '../.env')) # Intenta cargarlo de la carpeta raíz

def analizar_con_ia(prompt: str) -> str:
    """Llama a Groq API usando Llama 3.1 y devuelve el análisis."""
    try:
        # Ahora sí coincidirá con el nombre corregido del .env
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        
        if not api_key:
            return "⚠️ Error: No se encontró la GROQ_API_KEY en el archivo .env"

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        data = resp.json()
        
        if "error" in data:
            print("Error de Groq API:", data["error"])
            return f"⚠️ Error de la IA (Groq): {data['error'].get('message', 'Desconocido')}"
            
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
            
        return "⚠️ No se pudo obtener análisis de IA en este momento."
        
    except Exception as e:
        return f"⚠️ Error al conectar con Groq: {str(e)}"

# ═══════════════════════════════════════════════════════════
# REPORTE 1 – Análisis General del Sistema
# ═══════════════════════════════════════════════════════════
@reportes_ia_bp.route('/reporte1')
@login_required
def reporte1():
    # ── Métricas generales ──
    total_estudiantes   = Estudiante.query.count()
    total_inscripciones = InscripcionPostulante.query.count()
    total_pagos         = AporizacionDePago.query.count()
    monto_total         = db.session.query(func.sum(AporizacionDePago.monto)).scalar() or 0
    monto_promedio      = db.session.query(func.avg(AporizacionDePago.monto)).scalar() or 0
    total_carreras      = Carrera.query.count()
    total_usuarios      = Usuario.query.count()

    # ── Pagos por carrera (barras) ──
    pagos_carrera = db.session.query(
        Carrera.nombre_carrera,
        func.count(AporizacionDePago.id_pago).label('n_pagos'),
        func.sum(AporizacionDePago.monto).label('monto')
    ).join(InscripcionPostulante, Carrera.id_carrera == InscripcionPostulante.id_carrera)\
     .join(AporizacionDePago, InscripcionPostulante.id_inscripcion == AporizacionDePago.id_inscripcion)\
     .group_by(Carrera.nombre_carrera).all()

    # ── Estado inscripciones (pie) ──
    estado_insc = db.session.query(
        InscripcionPostulante.estado,
        func.count(InscripcionPostulante.id_inscripcion).label('total')
    ).group_by(InscripcionPostulante.estado).all()

    # ── Prompt para IA ──
    resumen = {
        "estudiantes": total_estudiantes,
        "inscripciones": total_inscripciones,
        "pagos_realizados": total_pagos,
        "monto_total_bs": round(monto_total, 2),
        "monto_promedio_bs": round(monto_promedio, 2),
        "carreras": total_carreras,
        "pagos_por_carrera": [
            {"carrera": r.nombre_carrera, "pagos": r.n_pagos, "monto": round(r.monto or 0, 2)}
            for r in pagos_carrera
        ],
        "inscripciones_por_estado": [
            {"estado": r.estado or "Sin estado", "total": r.total}
            for r in estado_insc
        ]
    }
    prompt = f"""Eres un analista experto en sistemas educativos. 
Analiza los siguientes datos del Sistema de Gestión de Pagos del Programa Especial de Titulación (PET-FNI):

{json.dumps(resumen, ensure_ascii=False, indent=2)}

Proporciona:
1. Un resumen ejecutivo del estado general del sistema (2-3 oraciones).
2. Los 3 hallazgos más importantes.
3. Dos recomendaciones concretas para mejorar la recaudación o la gestión.
4. Un semáforo de salud del sistema (Verde/Amarillo/Rojo) con justificación breve.

Responde en español, de forma clara y profesional. Usa viñetas para los puntos 2 y 3."""

    analisis_ia = analizar_con_ia(prompt)

    return render_template('reportes_ia/reporte1.html',
        total_estudiantes=total_estudiantes,
        total_inscripciones=total_inscripciones,
        total_pagos=total_pagos,
        monto_total=monto_total,
        monto_promedio=monto_promedio,
        total_carreras=total_carreras,
        total_usuarios=total_usuarios,
        pagos_carrera=pagos_carrera,
        estado_insc=estado_insc,
        analisis_ia=analisis_ia,
    )


# API JSON para gráfica reporte 1
@reportes_ia_bp.route('/api/r1/pagos-carrera')
@login_required
def api_r1_pagos_carrera():
    datos = db.session.query(
        Carrera.nombre_carrera,
        func.sum(AporizacionDePago.monto).label('monto')
    ).join(InscripcionPostulante, Carrera.id_carrera == InscripcionPostulante.id_carrera)\
     .join(AporizacionDePago, InscripcionPostulante.id_inscripcion == AporizacionDePago.id_inscripcion)\
     .group_by(Carrera.nombre_carrera).all()
    return jsonify({'labels': [d[0] for d in datos], 'data': [float(d[1] or 0) for d in datos]})


@reportes_ia_bp.route('/api/r1/estado-inscripciones')
@login_required
def api_r1_estado():
    datos = db.session.query(
        InscripcionPostulante.estado,
        func.count(InscripcionPostulante.id_inscripcion)
    ).group_by(InscripcionPostulante.estado).all()
    return jsonify({'labels': [d[0] or 'Sin estado' for d in datos], 'data': [d[1] for d in datos]})


# ═══════════════════════════════════════════════════════════
# REPORTE 2 – Tendencias y Comportamiento
# ═══════════════════════════════════════════════════════════
@reportes_ia_bp.route('/reporte2')
@login_required
def reporte2():
    # ── Pagos mensuales (línea) ──
    pagos_todos = AporizacionDePago.query.filter(
        AporizacionDePago.fecha_Autorizacion.isnot(None)
    ).all()
    mensuales = {}
    for p in pagos_todos:
        key = p.fecha_Autorizacion.strftime('%Y-%m')
        mensuales[key] = mensuales.get(key, 0) + (p.monto or 0)
    meses = sorted(mensuales.keys())
    montos_mes = [round(mensuales[m], 2) for m in meses]

    # ── Top 5 estudiantes ──
    top_est = db.session.query(
        Estudiante.nombre,
        func.count(AporizacionDePago.id_pago).label('n'),
        func.sum(AporizacionDePago.monto).label('total')
    ).join(InscripcionPostulante, Estudiante.id_Estudiante == InscripcionPostulante.id_estudiante)\
     .join(AporizacionDePago, InscripcionPostulante.id_inscripcion == AporizacionDePago.id_inscripcion)\
     .group_by(Estudiante.nombre)\
     .order_by(func.sum(AporizacionDePago.monto).desc())\
     .limit(5).all()

    # ── Inscripciones por carrera ──
    insc_carrera = db.session.query(
        Carrera.nombre_carrera,
        func.count(InscripcionPostulante.id_inscripcion).label('total')
    ).join(InscripcionPostulante, Carrera.id_carrera == InscripcionPostulante.id_carrera)\
     .group_by(Carrera.nombre_carrera).all()

    # ── Calcular tendencia (simple: último mes vs anterior) ──
    tendencia = "estable"
    cambio_pct = 0
    if len(montos_mes) >= 2:
        ultimo  = montos_mes[-1]
        anterior = montos_mes[-2]
        if anterior > 0:
            cambio_pct = round(((ultimo - anterior) / anterior) * 100, 1)
            tendencia = "crecimiento" if cambio_pct > 0 else "descenso"

    # ── Prompt IA ──
    datos_ia = {
        "tendencia_mensual": [{"mes": m, "monto": v} for m, v in zip(meses, montos_mes)],
        "top_estudiantes_pagadores": [
            {"nombre": r.nombre, "pagos": r.n, "total": round(r.total or 0, 2)} for r in top_est
        ],
        "inscripciones_por_carrera": [
            {"carrera": r.nombre_carrera, "inscripciones": r.total} for r in insc_carrera
        ],
        "tendencia_general": tendencia,
        "variacion_ultimo_mes_pct": cambio_pct
    }
    prompt = f"""Eres un analista de datos educativos y financieros. 
Analiza los siguientes patrones y tendencias del sistema PET-FNI:

{json.dumps(datos_ia, ensure_ascii=False, indent=2)}

Proporciona:
1. Interpretación de la tendencia mensual de pagos (¿hay crecimiento, estancamiento o descenso?).
2. Perfil de los estudiantes más comprometidos con sus pagos.
3. Qué carreras concentran más actividad y por qué podría ser.
4. Alertas sobre comportamientos anómalos o preocupantes en los datos.
5. Dos estrategias concretas para mejorar la tendencia de pagos.

Responde en español con viñetas y sé específico con los números."""

    analisis_ia = analizar_con_ia(prompt)

    return render_template('reportes_ia/reporte2.html',
        meses=json.dumps(meses),
        montos_mes=json.dumps(montos_mes),
        top_est=top_est,
        insc_carrera=insc_carrera,
        tendencia=tendencia,
        cambio_pct=cambio_pct,
        analisis_ia=analisis_ia,
    )



@reportes_ia_bp.route('/reporte3')
@login_required
def reporte3():
    # ── Datos para predicción ──
    pagos_todos = AporizacionDePago.query.filter(
        AporizacionDePago.fecha_Autorizacion.isnot(None)
    ).all()

    mensuales = {}
    for p in pagos_todos:
        key = p.fecha_Autorizacion.strftime('%Y-%m')
        mensuales[key] = mensuales.get(key, 0) + (p.monto or 0)
    meses_ord = sorted(mensuales.keys())
    valores   = [mensuales[m] for m in meses_ord]

    # ── Predicción simple: promedio móvil 3 meses ──
    prediccion_meses = []
    prediccion_vals  = []
    if len(valores) >= 3:
        ultimo_mes = meses_ord[-1]
        avg3 = sum(valores[-3:]) / 3
        # Generar 3 meses futuros
        from datetime import datetime
        base = datetime.strptime(ultimo_mes, '%Y-%m')
        for i in range(1, 4):
            m = base.replace(day=1)
            month = m.month + i
            year  = m.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            prediccion_meses.append(f"{year}-{month:02d}")
            factor = 1.05 if len(valores) >= 2 and valores[-1] > valores[-2] else 1.0
            prediccion_vals.append(round(avg3 * (factor ** i), 2))
    else:
        prediccion_meses = ['Sin datos suficientes']
        prediccion_vals  = [0]

    # ── Riesgo de morosidad por carrera ──
    riesgo = db.session.query(
        Carrera.nombre_carrera,
        func.count(InscripcionPostulante.id_inscripcion).label('inscritos'),
        func.count(AporizacionDePago.id_pago).label('pagos')
    ).join(InscripcionPostulante, Carrera.id_carrera == InscripcionPostulante.id_carrera)\
     .outerjoin(AporizacionDePago, InscripcionPostulante.id_inscripcion == AporizacionDePago.id_inscripcion)\
     .group_by(Carrera.nombre_carrera).all()

    riesgo_data = []
    for r in riesgo:
        tasa_pago = (r.pagos / r.inscritos * 100) if r.inscritos > 0 else 0
        nivel = 'Alto' if tasa_pago < 30 else ('Medio' if tasa_pago < 70 else 'Bajo')
        riesgo_data.append({
            'carrera': r.nombre_carrera,
            'inscritos': r.inscritos,
            'pagos': r.pagos,
            'tasa_pago': round(tasa_pago, 1),
            'nivel_riesgo': nivel
        })

    # ── Total recaudado vs proyectado ──
    total_recaudado = sum(valores)
    total_proyectado = sum(prediccion_vals)

    # ── Prompt IA predicción y recomendaciones ──
    datos_ia = {
        "historial_pagos_mensual": [{"mes": m, "monto": round(v, 2)} for m, v in zip(meses_ord, valores)],
        "prediccion_proximos_3_meses": [{"mes": m, "monto_proyectado": v} for m, v in zip(prediccion_meses, prediccion_vals)],
        "riesgo_morosidad_por_carrera": riesgo_data,
        "total_recaudado_historico": round(total_recaudado, 2),
        "total_proyectado_proximos_3_meses": round(total_proyectado, 2)
    }
    prompt = f"""Eres un sistema de inteligencia artificial especializado en análisis financiero educativo.
Basándote en los datos históricos y proyecciones del sistema PET-FNI:

{json.dumps(datos_ia, ensure_ascii=False, indent=2)}

Proporciona:
1. PREDICCIÓN: Evalúa si la proyección de pagos para los próximos 3 meses es optimista, conservadora o pesimista y por qué.
2. RIESGO DE MOROSIDAD: Identifica qué carreras representan mayor riesgo de impago y recomienda acciones específicas para cada una.
3. RECOMENDACIONES DE IA (mínimo 4):
   - Estrategias para reducir la morosidad
   - Acciones para aumentar la recaudación
   - Optimización de inscripciones
   - Propuesta de incentivo para pagos anticipados
4. CLASIFICACIÓN AUTOMÁTICA: Clasifica el sistema en una de estas categorías y justifica:
   - 🟢 Sistema Saludable
   - 🟡 Sistema en Riesgo Moderado  
   - 🔴 Sistema en Riesgo Crítico

Sé preciso, usa los números reales del sistema y da recomendaciones accionables."""

    analisis_ia = analizar_con_ia(prompt)

    return render_template('reportes_ia/reporte3.html',
        meses_ord=json.dumps(meses_ord),
        valores=json.dumps([round(v, 2) for v in valores]),
        prediccion_meses=json.dumps(prediccion_meses),
        prediccion_vals=json.dumps(prediccion_vals),
        riesgo_data=riesgo_data,
        total_recaudado=round(total_recaudado, 2),
        total_proyectado=round(total_proyectado, 2),
        analisis_ia=analisis_ia,
    )