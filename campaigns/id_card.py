"""
Volunteer ID Card PDF generator using reportlab.

Reuses the same Bengali-text-as-image approach as accounts/receipt.py
(see that file for the full explanation of *why* this is needed — short
version: reportlab can't shape Bengali conjuncts/vowel-signs on its own).
Rather than duplicating that logic, we import the two small helpers from
accounts.receipt directly.
"""
from io import BytesIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.pathobject import PDFPathObject
from django.conf import settings
from django.contrib.staticfiles import finders
from PIL import Image as PILImage

from accounts.receipt import _contains_non_ascii, _render_unicode_text_image

# Standard CR80 card size (the size of a real bank/ID card), landscape.
CARD_WIDTH = 85.6 * mm
CARD_HEIGHT = 54 * mm

GREEN = colors.HexColor('#15803d')
DARK_GREEN = colors.HexColor('#0f5c2e')
GRAY = colors.HexColor('#6b7280')
DARK = colors.HexColor('#111827')
WHITE = colors.white


def _bengali_safe_text(c, x, y, text, font_size, color_rgb, font='Helvetica', bold=False, max_width_pt=None):
    """Draw `text` at (x, y) — as real PDF text if it's plain ASCII, or as a
    rasterized (correctly-shaped) image if it contains Bengali/non-ASCII."""
    text = '' if text is None else str(text)
    if _contains_non_ascii(text):
        img_flowable = _render_unicode_text_image(
            text, font_size=font_size, color_rgb=color_rgb,
            max_width_pt=max_width_pt or 200,
        )
        # RLImage flowables need to be drawn via drawOn with their own w/h
        img_flowable.drawOn(c, x, y)
        return img_flowable.drawWidth
    else:
        c.setFont(f"{font}-Bold" if bold else font, font_size)
        r, g, b = [v / 255 for v in color_rgb]
        c.setFillColorRGB(r, g, b)
        c.drawString(x, y, text)
        return c.stringWidth(text, f"{font}-Bold" if bold else font, font_size)


def _make_qr_image(url, box_size=6):
    qr = qrcode.QRCode(border=1, box_size=box_size)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#111827", back_color="white").convert('RGB')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


# Cached so we only read + re-process the logo file once per process, not
# once per PDF generated.
_LOGO_PIL_CACHE = None


def _get_logo_pil():
    global _LOGO_PIL_CACHE
    if _LOGO_PIL_CACHE is None:
        path = finders.find('img/logo_transparent.png')
        if path:
            _LOGO_PIL_CACHE = PILImage.open(path).convert('RGBA')
        else:
            _LOGO_PIL_CACHE = False  # tried and failed — don't keep retrying
    return _LOGO_PIL_CACHE or None


def _logo_reader():
    logo = _get_logo_pil()
    if not logo:
        return None
    buf = BytesIO()
    logo.save(buf, format='PNG')
    buf.seek(0)
    return ImageReader(buf)


def _watermark_logo_reader(opacity=0.06):
    """A large, very faint copy of the logo for the card background — the
    same kind of subtle security/branding texture real ID cards use, so the
    card doesn't read as flat/empty behind the main text."""
    logo = _get_logo_pil()
    if not logo:
        return None
    faded = logo.copy()
    r, g, b, a = faded.split()
    a = a.point(lambda v: int(v * opacity))
    faded.putalpha(a)
    buf = BytesIO()
    faded.save(buf, format='PNG')
    buf.seek(0)
    return ImageReader(buf)


def generate_volunteer_id_card_pdf(volunteer, verify_url):
    """Returns a BytesIO containing a single-page, credit-card-sized PDF
    (front side only) for the given approved Volunteer."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(CARD_WIDTH, CARD_HEIGHT))

    # ── Rounded-corner card body — clip everything else to this shape, like
    # a real plastic ID card instead of a plain rectangle. ──
    radius = 3 * mm
    clip_path = c.beginPath()
    clip_path.roundRect(0, 0, CARD_WIDTH, CARD_HEIGHT, radius)
    c.clipPath(clip_path, stroke=0, fill=0)

    # ── Background ──
    c.setFillColor(WHITE)
    c.rect(0, 0, CARD_WIDTH, CARD_HEIGHT, fill=1, stroke=0)

    # ── Faint logo watermark, behind everything else ──
    watermark = _watermark_logo_reader(opacity=0.07)
    if watermark:
        wm_size = 40 * mm
        c.drawImage(
            watermark, CARD_WIDTH - wm_size + 6 * mm, -8 * mm,
            width=wm_size, height=wm_size, mask='auto',
        )

    # ── Header bar ──
    header_h = 12 * mm
    c.setFillColor(GREEN)
    c.rect(0, CARD_HEIGHT - header_h, CARD_WIDTH, header_h, fill=1, stroke=0)

    # White circular badge with the real Sohay.bd logo inside it
    badge_d = 9 * mm
    badge_cx = 4 * mm + badge_d / 2
    badge_cy = CARD_HEIGHT - header_h / 2
    c.setFillColor(WHITE)
    c.circle(badge_cx, badge_cy, badge_d / 2, fill=1, stroke=0)
    logo = _logo_reader()
    if logo:
        logo_d = badge_d - 1.6 * mm
        c.drawImage(
            logo, badge_cx - logo_d / 2, badge_cy - logo_d / 2,
            width=logo_d, height=logo_d, mask='auto', preserveAspectRatio=True,
        )

    text_start_x = 4 * mm + badge_d + 2.5 * mm
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(text_start_x, CARD_HEIGHT - header_h + 3.7 * mm, "Sohay.bd")
    c.setFont('Helvetica', 6)
    c.drawString(text_start_x, CARD_HEIGHT - header_h + 1 * mm, "VOLUNTEER IDENTITY CARD")

    # ── Footer bar ──
    footer_h = 6 * mm
    c.setFillColor(DARK_GREEN)
    c.rect(0, 0, CARD_WIDTH, footer_h, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica', 6)
    c.drawCentredString(CARD_WIDTH / 2, 2 * mm, f"{settings.SITE_DOMAIN}  |  Verify: scan QR")

    # ── Photo ──
    photo_x = 4 * mm
    photo_y = footer_h + 3 * mm
    photo_w = 20 * mm
    photo_h = 24 * mm
    if volunteer.photo:
        try:
            c.drawImage(
                volunteer.photo.path, photo_x, photo_y, width=photo_w, height=photo_h,
                preserveAspectRatio=True, anchor='n', mask='auto',
            )
        except Exception:
            _draw_photo_placeholder(c, photo_x, photo_y, photo_w, photo_h)
    else:
        _draw_photo_placeholder(c, photo_x, photo_y, photo_w, photo_h)
    c.setStrokeColor(colors.HexColor('#d1d5db'))
    c.setLineWidth(0.5)
    c.rect(photo_x, photo_y, photo_w, photo_h, fill=0, stroke=1)

    # ── Text block (name, ID, role, valid-since) ──
    text_x = photo_x + photo_w + 4 * mm
    text_top = CARD_HEIGHT - header_h - 4 * mm
    max_w = CARD_WIDTH - text_x - 4 * mm

    y = text_top
    _bengali_safe_text(c, text_x, y, volunteer.name, font_size=10.5, color_rgb=(17, 24, 39), bold=True, max_width_pt=max_w)

    # Small accent rule under the name for a bit of visual structure
    y -= 1.6 * mm
    c.setStrokeColor(GREEN)
    c.setLineWidth(1)
    c.line(text_x, y, text_x + 14 * mm, y)

    y -= 3.6 * mm
    c.setFont('Helvetica', 6.3)
    c.setFillColor(GRAY)
    c.drawString(text_x, y, "VOLUNTEER ID")
    y -= 3.6 * mm
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(DARK)
    c.drawString(text_x, y, volunteer.volunteer_id or "—")

    y -= 5.0 * mm
    c.setFont('Helvetica', 6.3)
    c.setFillColor(GRAY)
    c.drawString(text_x, y, "PROFESSION")
    y -= 3.6 * mm
    _bengali_safe_text(c, text_x, y, volunteer.profession, font_size=8, color_rgb=(17, 24, 39), max_width_pt=max_w - 20*mm)

    y -= 5.0 * mm
    c.setFont('Helvetica', 6.3)
    c.setFillColor(GRAY)
    c.drawString(text_x, y, "VALID SINCE")
    y -= 3.6 * mm
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(DARK)
    valid_since = volunteer.approved_at.strftime('%d %b %Y') if volunteer.approved_at else "—"
    c.drawString(text_x, y, valid_since)

    # ── QR code (bottom-right, above footer) ──
    qr_size = 15 * mm
    qr_x = CARD_WIDTH - qr_size - 4 * mm
    qr_y = footer_h + 3 * mm
    qr_buf = _make_qr_image(verify_url)
    c.setFillColor(WHITE)
    c.rect(qr_x - 1 * mm, qr_y - 1 * mm, qr_size + 2 * mm, qr_size + 2 * mm, fill=1, stroke=0)
    c.drawImage(ImageReader(qr_buf), qr_x, qr_y, width=qr_size, height=qr_size)

    # ── Thin overall border so the rounded-corner edge reads crisply ──
    c.setStrokeColor(colors.HexColor('#d1d5db'))
    c.setLineWidth(0.75)
    border_path = c.beginPath()
    border_path.roundRect(0.5, 0.5, CARD_WIDTH - 1, CARD_HEIGHT - 1, radius)
    c.drawPath(border_path, fill=0, stroke=1)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def _draw_photo_placeholder(c, x, y, w, h):
    c.setFillColor(colors.HexColor('#e5f5ea'))
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(x + w / 2, y + h / 2 - 5, "?")
