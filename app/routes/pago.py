import os
import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, current_app
from flask_login import login_required
from app.models import AporizacionDePago, InscripcionPostulante
from app import db
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

pago_bp = Blueprint('pago', __name__, url_prefix='/pago')


def numero_a_literal(monto):
    """Convierte número a texto en español (simplificado)."""
    try:
        entero = int(monto)
        decimales = round((monto - entero) * 100)
        unidades = ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve',
                    'diez', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete',
                    'dieciocho', 'diecinueve']
        decenas = ['', 'diez', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
        centenas = ['', 'cien', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos',
                    'seiscientos', 'setecientos', 'ochocientos', 'novecientos']

        def convertir_cientos(n):
            if n == 0: return ''
            if n < 20: return unidades[n]
            if n < 100:
                u = unidades[n % 10]
                d = decenas[n // 10]
                return d + (' y ' + u if u else '')
            c = centenas[n // 100]
            resto = convertir_cientos(n % 100)
            if n // 100 == 1 and n % 100 > 0: c = 'ciento'
            return c + (' ' + resto if resto else '')

        if entero == 0:
            texto = 'cero'
        elif entero < 1000:
            texto = convertir_cientos(entero)
        elif entero < 1000000:
            miles = entero // 1000
            resto = entero % 1000
            texto_miles = 'mil' if miles == 1 else convertir_cientos(miles) + ' mil'
            texto = texto_miles + (' ' + convertir_cientos(resto) if resto else '')
        else:
            texto = str(entero)

        return texto.capitalize() + f' {decimales:02d}/100 bolivianos'
    except:
        return f'{monto} bolivianos'


def generar_pdf_pago(pago):
    """Genera el recibo de autorización de pago en PDF estilo FNI."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    azul_fni = colors.HexColor('#1a237e')
    azul_claro = colors.HexColor('#283593')

    estilo_titulo = ParagraphStyle('titulo', fontName='Helvetica-Bold', fontSize=13,
                                   textColor=azul_fni, alignment=TA_CENTER)
    estilo_sub = ParagraphStyle('sub', fontName='Helvetica', fontSize=9,
                                textColor=colors.black, alignment=TA_CENTER)
    estilo_bold = ParagraphStyle('bold', fontName='Helvetica-Bold', fontSize=10,
                                 textColor=colors.white, alignment=TA_CENTER,
                                 backColor=azul_fni)
    estilo_normal = ParagraphStyle('normal', fontName='Helvetica', fontSize=10)
    estilo_valor = ParagraphStyle('valor', fontName='Helvetica-Bold', fontSize=11, textColor=azul_fni)

    inscripcion = pago.inscripcion
    estudiante = inscripcion.estudiante
    carrera = inscripcion.carrera

    # CABECERA - dos columnas: logo+info | número
    header_data = [
        [
            Paragraph('<b>PROGRAMA ESPECIAL DE TITULACIÓN</b>', estilo_titulo),
            Paragraph('<b>P.E.T. 2025</b>', ParagraphStyle('pet', fontName='Helvetica-Bold',
                      fontSize=12, textColor=azul_fni, alignment=TA_CENTER,
                      borderColor=azul_fni, borderWidth=1))
        ],
        [
            Paragraph('Teléfono: 52-64544<br/>Correo electrónico: fnipet@gmail.com', estilo_sub),
            Paragraph('<b>AUTORIZACIÓN ELECTRÓNICA</b>', ParagraphStyle('auth', fontName='Helvetica-Bold',
                      fontSize=10, textColor=colors.white, alignment=TA_CENTER,
                      backColor=azul_fni))
        ],
        [
            Paragraph('<b>1ra cuota</b>', ParagraphStyle('cuota', fontName='Helvetica-Bold',
                      fontSize=16, textColor=azul_fni, alignment=TA_CENTER)),
            Paragraph(f'<b>Nro {pago.id_pago:05d}</b>', ParagraphStyle('nro', fontName='Helvetica-Bold',
                      fontSize=12, textColor=azul_fni, alignment=TA_CENTER))
        ]
    ]
    header_table = Table(header_data, colWidths=[9*cm, 7.5*cm])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, azul_fni),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, azul_fni),
        ('BACKGROUND', (1, 1), (1, 1), azul_fni),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (1, 0), (1, 0), [colors.HexColor('#e8eaf6')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))

    # DATOS DEL POSTULANTE
    fecha_emision = pago.fecha_Autorizacion.strftime('%d/%m/%Y') if pago.fecha_Autorizacion else 'N/A'
    info_data = [
        [
            Paragraph(f'<b>POSTULANTE:</b> {estudiante.nombre}', estilo_normal),
            Paragraph(f'<b>FECHA DE EMISIÓN:</b> {fecha_emision}', estilo_normal)
        ],
        [
            Paragraph(f'<b>CI:</b> {estudiante.ci}', estilo_normal),
            Paragraph('<b>MONEDA:</b> Bolivianos', estilo_normal)
        ],
        [
            Paragraph(f'<b>CARRERA:</b> {carrera.nombre_carrera}', estilo_normal),
            Paragraph('', estilo_normal)
        ],
    ]

    # Foto del estudiante
    foto_cell = ''
    if estudiante.foto:
        foto_path = os.path.join(current_app.root_path, 'static', 'uploads', estudiante.foto)
        if os.path.exists(foto_path):
            try:
                img = RLImage(foto_path, width=2.5*cm, height=2.5*cm)
                foto_cell = img
            except:
                foto_cell = Paragraph('Sin foto', estilo_normal)

    info_table = Table(info_data, colWidths=[10*cm, 6.5*cm])
    info_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, azul_fni),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#c5cae9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    # IMPORTE
    literal = numero_a_literal(pago.monto or 0)
    monto_data = [
        [
            Paragraph('Aporte Facultativo\n(Aux: PET-FNI 2025 Facultativo):', estilo_normal),
            Paragraph(f'<b>IMPORTE: {pago.monto:,.2f}</b>', estilo_valor)
        ],
        [
            '',
            Paragraph(f'<b>LITERAL:</b> {literal}', estilo_normal)
        ]
    ]
    monto_table = Table(monto_data, colWidths=[6*cm, 10.5*cm])
    monto_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, azul_fni),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#c5cae9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('SPAN', (0, 0), (0, 1)),
    ]))
    story.append(monto_table)
    story.append(Spacer(1, 0.4*cm))

    # FOOTER - QR placeholder + aviso
    aviso = ('FECHA LÍMITE DE PAGO: El presente recibo debe ser cancelado en un plazo '
             'máximo de 48 horas hábiles a partir de la fecha de su emisión, '
             'caso contrario quedará nulo.')
    footer_data = [
        [
            Paragraph('<b>[QR]</b>', ParagraphStyle('qr', fontName='Helvetica-Bold', fontSize=28,
                      textColor=azul_fni, alignment=TA_CENTER)),
            Paragraph(aviso, estilo_normal)
        ]
    ]
    footer_table = Table(footer_data, colWidths=[4*cm, 12.5*cm])
    footer_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, azul_fni),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, azul_fni),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(footer_table)

    # Firma
    story.append(Spacer(1, 1.5*cm))
    firma_data = [
        [Paragraph('______________________________', estilo_sub),
         Paragraph('______________________________', estilo_sub)],
        [Paragraph('<b>Responsable</b>', estilo_sub),
         Paragraph(f'<b>{inscripcion.usuario.username}</b>', estilo_sub)]
    ]
    firma_table = Table(firma_data, colWidths=[8.25*cm, 8.25*cm])
    story.append(firma_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


@pago_bp.route('/')
@login_required
def listar():
    pagos = AporizacionDePago.query.all()
    return render_template('pago/listar.html', pagos=pagos)


@pago_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    inscripciones = InscripcionPostulante.query.all()
    if request.method == 'POST':
        fecha_str = request.form.get('fecha_Autorizacion')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        pago = AporizacionDePago(
            id_inscripcion=request.form.get('id_inscripcion'),
            fecha_Autorizacion=fecha,
            monto=request.form.get('monto')
        )
        db.session.add(pago)
        db.session.commit()
        flash('Pago registrado correctamente.', 'success')
        return redirect(url_for('pago.listar'))
    return render_template('pago/form.html', pago=None, inscripciones=inscripciones)


@pago_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    pago = AporizacionDePago.query.get_or_404(id)
    inscripciones = InscripcionPostulante.query.all()
    if request.method == 'POST':
        pago.id_inscripcion = request.form.get('id_inscripcion')
        fecha_str = request.form.get('fecha_Autorizacion')
        pago.fecha_Autorizacion = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        pago.monto = request.form.get('monto')
        db.session.commit()
        flash('Pago actualizado.', 'success')
        return redirect(url_for('pago.listar'))
    return render_template('pago/form.html', pago=pago, inscripciones=inscripciones)


@pago_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    pago = AporizacionDePago.query.get_or_404(id)
    db.session.delete(pago)
    db.session.commit()
    flash('Pago eliminado.', 'success')
    return redirect(url_for('pago.listar'))


@pago_bp.route('/pdf/<int:id>')
@login_required
def exportar_pdf(id):
    pago = AporizacionDePago.query.get_or_404(id)
    buffer = generar_pdf_pago(pago)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=autorizacion_pago_{pago.id_pago:05d}.pdf'
    return response
