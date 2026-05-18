import io
import os
from flask import Blueprint, render_template, jsonify, make_response, current_app
from flask_login import login_required
from app.models import AporizacionDePago, InscripcionPostulante, Carrera, Estudiante, Usuario
from app import db
from sqlalchemy import func
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')


def get_data_reportes():
    pagos_por_carrera = db.session.query(
        Carrera.nombre_carrera,
        func.count(AporizacionDePago.id_pago).label('total_pagos'),
        func.sum(AporizacionDePago.monto).label('monto_total'),
        func.avg(AporizacionDePago.monto).label('monto_promedio')
    ).join(InscripcionPostulante, Carrera.id_carrera == InscripcionPostulante.id_carrera)\
     .join(AporizacionDePago, InscripcionPostulante.id_inscripcion == AporizacionDePago.id_inscripcion)\
     .group_by(Carrera.nombre_carrera).all()

    inscripciones_estado = db.session.query(
        InscripcionPostulante.estado,
        func.count(InscripcionPostulante.id_inscripcion).label('total')
    ).group_by(InscripcionPostulante.estado).all()

    top_estudiantes = db.session.query(
        Estudiante.nombre,
        Estudiante.foto,
        func.count(AporizacionDePago.id_pago).label('num_pagos'),
        func.sum(AporizacionDePago.monto).label('total_pagado')
    ).join(InscripcionPostulante, Estudiante.id_Estudiante == InscripcionPostulante.id_estudiante)\
     .join(AporizacionDePago, InscripcionPostulante.id_inscripcion == AporizacionDePago.id_inscripcion)\
     .group_by(Estudiante.nombre, Estudiante.foto)\
     .order_by(func.sum(AporizacionDePago.monto).desc())\
     .limit(5).all()

    return pagos_por_carrera, inscripciones_estado, top_estudiantes


@reportes_bp.route('/')
@login_required
def index():
    pagos_por_carrera, inscripciones_estado, top_estudiantes = get_data_reportes()
    return render_template('reportes/index.html',
                           pagos_por_carrera=pagos_por_carrera,
                           inscripciones_estado=inscripciones_estado,
                           top_estudiantes=top_estudiantes)


@reportes_bp.route('/api/pagos-carrera')
@login_required
def api_pagos_carrera():
    datos = db.session.query(
        Carrera.nombre_carrera,
        func.sum(AporizacionDePago.monto).label('monto_total')
    ).join(InscripcionPostulante, Carrera.id_carrera == InscripcionPostulante.id_carrera)\
     .join(AporizacionDePago, InscripcionPostulante.id_inscripcion == AporizacionDePago.id_inscripcion)\
     .group_by(Carrera.nombre_carrera).all()
    return jsonify({'labels': [d[0] for d in datos], 'data': [float(d[1] or 0) for d in datos]})


@reportes_bp.route('/api/inscripciones-estado')
@login_required
def api_inscripciones_estado():
    datos = db.session.query(
        InscripcionPostulante.estado,
        func.count(InscripcionPostulante.id_inscripcion).label('total')
    ).group_by(InscripcionPostulante.estado).all()
    return jsonify({'labels': [d[0] or 'Sin estado' for d in datos], 'data': [d[1] for d in datos]})


@reportes_bp.route('/api/pagos-mensuales')
@login_required
def api_pagos_mensuales():
    pagos = AporizacionDePago.query.filter(AporizacionDePago.fecha_Autorizacion.isnot(None)).all()
    mensuales = {}
    for p in pagos:
        key = p.fecha_Autorizacion.strftime('%Y-%m')
        mensuales[key] = mensuales.get(key, 0) + (p.monto or 0)
    meses_ordenados = sorted(mensuales.keys())
    return jsonify({'labels': meses_ordenados, 'data': [mensuales[m] for m in meses_ordenados]})


@reportes_bp.route('/pdf')
@login_required
def exportar_pdf():
    pagos_por_carrera, inscripciones_estado, top_estudiantes = get_data_reportes()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    azul = colors.HexColor('#1a237e')
    story = []

    # ---- ENCABEZADO ----
    estilo_h1 = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=18,
                               textColor=azul, alignment=TA_CENTER, spaceAfter=4)
    estilo_h2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=13,
                               textColor=azul, spaceBefore=14, spaceAfter=6)
    estilo_sub = ParagraphStyle('sub', fontName='Helvetica', fontSize=10,
                                textColor=colors.grey, alignment=TA_CENTER, spaceAfter=12)
    estilo_normal = ParagraphStyle('n', fontName='Helvetica', fontSize=9)

    story.append(Paragraph('SISTEMA DE GESTIÓN DE PAGOS', estilo_h1))
    story.append(Paragraph('Programa Especial de Titulación — Reporte Estadístico General', estilo_sub))
    story.append(HRFlowable(width='100%', thickness=2, color=azul))
    story.append(Spacer(1, 0.5*cm))

    # ---- TABLA: Pagos por carrera ----
    story.append(Paragraph('1. Resumen de Pagos por Carrera', estilo_h2))
    if pagos_por_carrera:
        header = [['Carrera', 'Total Pagos', 'Monto Total (Bs.)', 'Promedio (Bs.)']]
        rows = [[r.nombre_carrera, str(r.total_pagos),
                 f'{r.monto_total or 0:,.2f}', f'{r.monto_promedio or 0:,.2f}']
                for r in pagos_por_carrera]
        t = Table(header + rows, colWidths=[7*cm, 3*cm, 4.5*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), azul),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
            ('BOX', (0, 0), (-1, -1), 1, azul),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#c5cae9')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
    else:
        story.append(Paragraph('Sin datos registrados.', estilo_normal))

    story.append(Spacer(1, 0.6*cm))

    # ---- GRÁFICA BARRAS (ReportLab) ----
    if pagos_por_carrera:
        story.append(Paragraph('2. Gráfica — Monto Total por Carrera', estilo_h2))
        d = Drawing(400, 180)
        bc = VerticalBarChart()
        bc.x = 60; bc.y = 20; bc.height = 140; bc.width = 320
        valores = [float(r.monto_total or 0) for r in pagos_por_carrera]
        bc.data = [valores]
        bc.categoryAxis.categoryNames = [r.nombre_carrera[:15] for r in pagos_por_carrera]
        bc.bars[0].fillColor = colors.HexColor('#3949ab')
        bc.valueAxis.valueMin = 0
        bc.categoryAxis.labels.angle = 20
        bc.categoryAxis.labels.fontSize = 7
        d.add(bc)
        story.append(d)
        story.append(Spacer(1, 0.4*cm))

    # ---- TABLA: Estado inscripciones ----
    story.append(Paragraph('3. Inscripciones por Estado', estilo_h2))
    if inscripciones_estado:
        header2 = [['Estado', 'Total Inscripciones']]
        rows2 = [[r.estado or 'Sin estado', str(r.total)] for r in inscripciones_estado]
        t2 = Table(header2 + rows2, colWidths=[8*cm, 6.5*cm])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), azul),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
            ('BOX', (0, 0), (-1, -1), 1, azul),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#c5cae9')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t2)
    else:
        story.append(Paragraph('Sin datos registrados.', estilo_normal))

    story.append(Spacer(1, 0.6*cm))

    # ---- TABLA: Top estudiantes CON FOTO ----
    story.append(Paragraph('4. Top Estudiantes — Mayor Monto Pagado', estilo_h2))
    if top_estudiantes:
        header3 = [['Foto', 'Estudiante', 'N° Pagos', 'Total Pagado (Bs.)']]
        rows3 = []
        for r in top_estudiantes:
            foto_cell = ''
            if r.foto:
                foto_path = os.path.join(current_app.root_path, 'static', 'uploads', r.foto)
                if os.path.exists(foto_path):
                    try:
                        foto_cell = RLImage(foto_path, width=1.5*cm, height=1.5*cm)
                    except:
                        foto_cell = 'Sin foto'
            rows3.append([foto_cell, r.nombre, str(r.num_pagos), f'{r.total_pagado or 0:,.2f}'])
        t3 = Table(header3 + rows3, colWidths=[2*cm, 8*cm, 2.5*cm, 4*cm])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), azul),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
            ('BOX', (0, 0), (-1, -1), 1, azul),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#c5cae9')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t3)

    # Pie de página
    story.append(Spacer(1, 1.5*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=azul))
    from datetime import datetime
    story.append(Paragraph(f'Generado el {datetime.now().strftime("%d/%m/%Y %H:%M")} — Sistema de Gestión de Pagos FNI',
                           ParagraphStyle('foot', fontName='Helvetica', fontSize=8,
                                         textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_estadistico.pdf'
    return response
