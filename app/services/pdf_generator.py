from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.config import settings


def generar_pdf_orden(datos, output_path, currency_symbol=None):
    if currency_symbol is None:
        currency_symbol = settings.CURRENCY_SYMBOL
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor('#1a1a1a'),
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.HexColor('#666666'),
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=5,
    )

    # Header
    story.append(Paragraph("BikerZone - Orden de Servicio", title_style))
    story.append(Paragraph(f"Codigo: {datos['codigo']}", subtitle_style))
    story.append(Spacer(1, 20))

    # Info Cliente
    story.append(Paragraph("<b>Informacion del Cliente</b>", styles['Heading3']))
    cliente_data = [
        ['Nombre', datos['cliente']['nombre']],
        ['Telefono', datos['cliente']['telefono']],
        ['Email', datos['cliente']['email']],
    ]
    cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
    ]))
    story.append(cliente_table)
    story.append(Spacer(1, 20))

    # Info Moto
    story.append(Paragraph("<b>Informacion de la Moto</b>", styles['Heading3']))
    moto_data = [
        ['Marca', datos['moto']['marca']],
        ['Modelo', datos['moto']['modelo']],
        ['Placa', datos['moto']['placa']],
        ['Año', str(datos['moto']['anio'])],
        ['Kilometraje', f"{datos['moto']['kilometraje']} km"],
    ]
    moto_table = Table(moto_data, colWidths=[2*inch, 4*inch])
    moto_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
    ]))
    story.append(moto_table)
    story.append(Spacer(1, 20))

    # Detalles de la reparacion
    story.append(Paragraph("<b>Detalles de la Reparacion</b>", styles['Heading3']))
    story.append(Paragraph(f"<b>Falla Reportada:</b> {datos['falla_reportada']}", normal_style))
    if datos['diagnostico']:
        story.append(Paragraph(f"<b>Diagnostico:</b> {datos['diagnostico']}", normal_style))
    story.append(Spacer(1, 10))

    # Repuestos
    if datos['repuestos']:
        story.append(Paragraph("<b>Repuestos Utilizados</b>", styles['Heading3']))
        rep_headers = ['Repuesto', 'Cantidad', 'Precio Unit.', 'Subtotal']
        rep_data = [rep_headers]
        for r in datos['repuestos']:
            rep_data.append([
                r['nombre'],
                str(r['cantidad']),
                f"{currency_symbol}{r['precio_unitario']:.2f}",
                f"{currency_symbol}{r['subtotal']:.2f}",
            ])
        rep_data.append(['', '', 'Subtotal:', f"{currency_symbol}{datos['subtotal_repuestos']:.2f}"])

        rep_table = Table(rep_data, colWidths=[3*inch, 1*inch, 1.2*inch, 1.2*inch])
        rep_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ]))
        story.append(rep_table)
        story.append(Spacer(1, 20))

    # Totales
    story.append(Paragraph("<b>Totales</b>", styles['Heading3']))
    totales_data = [
        ['Presupuesto:', f"{currency_symbol}{datos['presupuesto']:.2f}"],
        ['Precio Final:', f"{currency_symbol}{datos['precio_final']:.2f}"],
    ]
    totales_table = Table(totales_data, colWidths=[4*inch, 2*inch])
    totales_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (1, -1), (1, -1), 12),
    ]))
    story.append(totales_table)
    story.append(Spacer(1, 20))

    # Fechas
    story.append(Paragraph(f"<b>Fecha Entrada:</b> {datos['fecha_entrada']}", normal_style))
    story.append(Paragraph(f"<b>Fecha Salida:</b> {datos['fecha_salida']}", normal_style))

    doc.build(story)
    return output_path
