"""
PDF Receipt generator using reportlab.
Generates a clean Bengali-friendly donation receipt.
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# Brand colours
GREEN  = colors.HexColor('#15803d')
LGREEN = colors.HexColor('#dcfce7')
GRAY   = colors.HexColor('#6b7280')
DARK   = colors.HexColor('#111827')


def generate_receipt_pdf(donation):
    """Return a BytesIO containing the PDF receipt for the given Donation."""
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18*mm,
        leftMargin=18*mm,
        topMargin=18*mm,
        bottomMargin=18*mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold',
        textColor=GREEN, alignment=TA_CENTER, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica',
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=4,
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica',
        textColor=GRAY,
    )
    value_style = ParagraphStyle(
        'Value', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold',
        textColor=DARK,
    )
    amount_style = ParagraphStyle(
        'Amount', parent=styles['Normal'],
        fontSize=26, fontName='Helvetica-Bold',
        textColor=GREEN, alignment=TA_CENTER,
    )
    note_style = ParagraphStyle(
        'Note', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica',
        textColor=GRAY, alignment=TA_CENTER,
    )

    story = []

    # ── HEADER ──
    story.append(Paragraph("Sahay.bd", title_style))
    story.append(Paragraph("Donation Receipt | sohay.pythonanywhere.com", subtitle_style))
    story.append(Paragraph("A CSR Initiative by Edumi", subtitle_style))
    story.append(HRFlowable(width='100%', thickness=2, color=GREEN, spaceAfter=10))

    # ── RECEIPT ID + DATE ──
    receipt_data = [
        [
            Paragraph("Receipt No.", label_style),
            Paragraph(f"#{donation.pk:06d}", value_style),
            Paragraph("Date", label_style),
            Paragraph(donation.created_at.strftime('%d %b %Y'), value_style),
        ]
    ]
    receipt_table = Table(receipt_data, colWidths=['20%','30%','15%','35%'])
    receipt_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LGREEN),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LGREEN]),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [4,4,4,4]),
    ]))
    story.append(receipt_table)
    story.append(Spacer(1, 14))

    # ── AMOUNT ──
    story.append(Paragraph(f"BDT {donation.amount:,.2f}", amount_style))
    story.append(Paragraph("Total Donation Amount", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#d1fae5'), spaceAfter=10))

    # ── DONOR + CAMPAIGN INFO ──
    rows = [
        ['Donor Name',      donation.display_name],
        ['Campaign',        donation.campaign.title],
        ['Payment Method',  donation.get_payment_method_display()],
        ['Reference',       donation.payment_reference or '—'],
        ['Status',          'Verified ✓'],
    ]
    if donation.donor_email:
        rows.insert(1, ['Email', donation.donor_email])

    table_data = []
    for lbl, val in rows:
        table_data.append([
            Paragraph(lbl, label_style),
            Paragraph(str(val), value_style),
        ])

    info_table = Table(table_data, colWidths=['35%','65%'])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f9fafb')),
        ('BACKGROUND', (1,0), (1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # ── THANK YOU ──
    story.append(HRFlowable(width='100%', thickness=2, color=GREEN, spaceBefore=4, spaceAfter=10))
    story.append(Paragraph(
        "Jazakallahu Khayran — May Allah reward you abundantly!",
        ParagraphStyle('Thanks', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=GREEN, alignment=TA_CENTER, spaceAfter=4)
    ))
    story.append(Paragraph(
        "This is a computer-generated receipt and does not require a signature.\n"
        "For queries: sahay@example.com | sohay.pythonanywhere.com",
        note_style,
    ))

    doc.build(story)
    buf.seek(0)
    return buf
