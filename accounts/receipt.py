"""
PDF Receipt generator using reportlab.
Generates a clean Bengali-friendly donation receipt.

── Bengali text handling ──────────────────────────────────────────────
reportlab draws text glyph-by-glyph and does NOT perform complex-script
text shaping. Bengali needs shaping (conjunct consonants like দ্দ, and
reordering of vowel signs like ে/ি which are typed after the consonant
but must be drawn before/around it) or the text renders as blank boxes
or garbled glyphs.

To fix this, any donor name / campaign title / payment method label
that contains Bengali (or other non-ASCII) text is rasterized separately
using Pillow's Raqm layout engine (HarfBuzz + FriBidi under the hood),
which shapes it correctly, and the result is embedded into the PDF as a
small transparent PNG instead of PDF text. Plain ASCII text (labels,
amounts, dates) is still drawn as normal PDF text — cheaper and crisper.
"""
from io import BytesIO
import re

from django.conf import settings
from PIL import Image as PILImage, ImageDraw, ImageFont

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    Image as RLImage,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# Brand colours
GREEN  = colors.HexColor('#15803d')
LGREEN = colors.HexColor('#dcfce7')
GRAY   = colors.HexColor('#6b7280')
DARK   = colors.HexColor('#111827')

# Bundled font that has Bengali glyphs (reportlab's built-in fonts don't).
BENGALI_FONT_PATH = settings.BASE_DIR / 'static' / 'fonts' / 'NotoSansBengali-Regular.ttf'

_NON_ASCII_RE = re.compile(r'[^\x00-\x7F]')


def _contains_non_ascii(text):
    return bool(_NON_ASCII_RE.search(text or ''))


def _render_unicode_text_image(text, font_size=10, color_rgb=(17, 24, 39), max_width_pt=260):
    """
    Rasterize `text` into a small transparent PNG using Pillow's Raqm text
    layout engine (proper Bengali shaping), and return it as a reportlab
    Image flowable sized in PDF points.
    """
    scale = 4  # supersample for crisp output on screen/print
    px_size = max(int(font_size * scale), 8)

    try:
        font = ImageFont.truetype(str(BENGALI_FONT_PATH), px_size, layout_engine=ImageFont.Layout.RAQM)
    except Exception:
        # Fall back to whatever default layout Pillow has if Raqm/font isn't available
        font = ImageFont.truetype(str(BENGALI_FONT_PATH), px_size)

    dummy = PILImage.new('RGBA', (10, 10))
    bbox = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font)
    pad = 6
    w = max(bbox[2] - bbox[0] + pad * 2, 1)
    h = max(bbox[3] - bbox[1] + pad * 2, 1)

    img = PILImage.new('RGBA', (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=color_rgb + (255,))

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    width_pt = w / scale
    height_pt = h / scale
    if width_pt > max_width_pt:
        ratio = max_width_pt / width_pt
        width_pt *= ratio
        height_pt *= ratio

    return RLImage(buf, width=width_pt, height=height_pt)


def _cell(text, style, color_rgb=(17, 24, 39)):
    """Table-cell flowable: plain ASCII -> normal Paragraph (crisp PDF text),
    anything with Bengali/non-ASCII characters -> rasterized image (correct shaping)."""
    text = '' if text is None else str(text)
    if _contains_non_ascii(text):
        return _render_unicode_text_image(text, font_size=style.fontSize, color_rgb=color_rgb)
    return Paragraph(text, style)


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
        fontSize=22, leading=27, fontName='Helvetica-Bold',
        textColor=GREEN, alignment=TA_CENTER, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        fontSize=10, leading=13, fontName='Helvetica',
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=4,
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=9, leading=12, fontName='Helvetica',
        textColor=GRAY,
    )
    value_style = ParagraphStyle(
        'Value', parent=styles['Normal'],
        fontSize=10, leading=13, fontName='Helvetica-Bold',
        textColor=DARK,
    )
    amount_style = ParagraphStyle(
        'Amount', parent=styles['Normal'],
        fontSize=26, leading=32, fontName='Helvetica-Bold',
        textColor=GREEN, alignment=TA_CENTER,
    )
    note_style = ParagraphStyle(
        'Note', parent=styles['Normal'],
        fontSize=8, leading=11, fontName='Helvetica',
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
    # NOTE: donor name, campaign title, and payment-method label are very
    # often Bengali (e.g. "বিকাশ") — these go through _cell() so they're
    # rasterized with correct shaping instead of coming out blank/garbled.
    rows = [
        ['Donor Name',      donation.display_name],
        ['Campaign',        donation.campaign.title],
        ['Payment Method',  donation.get_payment_method_display()],
        ['Reference',       donation.payment_reference or '—'],
        ['Status',          'Verified'],
    ]
    if donation.donor_email:
        rows.insert(1, ['Email', donation.donor_email])

    table_data = []
    for lbl, val in rows:
        table_data.append([
            Paragraph(lbl, label_style),
            _cell(val, value_style),
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
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # ── THANK YOU ──
    story.append(HRFlowable(width='100%', thickness=2, color=GREEN, spaceBefore=4, spaceAfter=10))
    story.append(Paragraph(
        "Jazakallahu Khayran — May Allah reward you abundantly!",
        ParagraphStyle('Thanks', parent=styles['Normal'],
            fontSize=11, leading=14, fontName='Helvetica-Bold',
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
