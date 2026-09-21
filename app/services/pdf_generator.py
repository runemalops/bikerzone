from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.config import settings


def generar_pdf_orden(datos, output_path, currency_symbol=None):
    if currency_symbol is None:
        currency_symbol = settings.CURRENCY_SYMBOL
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        textColor=colors.HexColor('#1a1a1a'),
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=6,
        textColor=colors.HexColor('#666666'),
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=3,
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=10,
        spaceAfter=4,
    )

    # Header
    story.append(Paragraph("BikerZone - Orden de Servicio", title_style))
    story.append(Paragraph(f"Codigo: {datos['codigo']}", subtitle_style))
    story.append(Spacer(1, 8))

    # Info Cliente y Moto lado a lado
    info_data = [
        ['Cliente', datos['cliente']['nombre'], 'Moto', f"{datos['moto']['marca']} {datos['moto']['modelo']}"],
        ['Telefono', datos['cliente']['telefono'], 'Placa', datos['moto']['placa']],
        ['Email', datos['cliente']['email'], 'Año', str(datos['moto']['anio'])],
        ['', '', 'Kilometraje', f"{datos['moto']['kilometraje']} km"],
    ]
    info_table = Table(info_data, colWidths=[1.1*inch, 2.4*inch, 1.1*inch, 2.4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8))

    # Detalles de la reparacion
    story.append(Paragraph("<b>Detalles de la Reparacion</b>", section_style))
    story.append(Paragraph(f"<b>Falla:</b> {datos['falla_reportada']}", normal_style))
    if datos['diagnostico']:
        story.append(Paragraph(f"<b>Diagnostico:</b> {datos['diagnostico']}", normal_style))

    # Repuestos
    if datos['repuestos']:
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Repuestos Utilizados</b>", section_style))
        rep_headers = ['Repuesto', 'Cant.', 'Precio Unit.', 'Subtotal']
        rep_data = [rep_headers]
        for r in datos['repuestos']:
            rep_data.append([
                r['nombre'],
                str(r['cantidad']),
                f"{currency_symbol}{r['precio_unitario']:.2f}",
                f"{currency_symbol}{r['subtotal']:.2f}",
            ])
        rep_data.append(['', '', 'Subtotal:', f"{currency_symbol}{datos['subtotal_repuestos']:.2f}"])

        rep_table = Table(rep_data, colWidths=[3.2*inch, 0.6*inch, 1.2*inch, 1.2*inch])
        rep_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ]))
        story.append(rep_table)

    # Totales y Fechas en tabla combinada
    story.append(Spacer(1, 8))
    summary_data = [
        ['Presupuesto:', f"{currency_symbol}{datos['presupuesto']:.2f}", 'Fecha Entrada:', datos['fecha_entrada']],
        ['Precio Final:', f"{currency_symbol}{datos['precio_final']:.2f}", 'Fecha Salida:', datos['fecha_salida']],
    ]
    summary_table = Table(summary_data, colWidths=[1.4*inch, 1.6*inch, 1.4*inch, 2.6*inch])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
    ]))
    story.append(summary_table)

    doc.build(story)
    return output_path
