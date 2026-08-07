"""
Donation "share card" — a 1080x1080 PNG generated on-demand (never written
to disk — see the view for why) for a donor to post to Facebook/Instagram/
WhatsApp after donating.

Uses Pillow's Raqm layout engine directly for Bengali text shaping, the
same underlying mechanism accounts/receipt.py uses for PDFs (see that
file's module docstring for the full explanation of why plain PIL/reportlab
text drawing doesn't work for Bengali on its own).
"""
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
from PIL import Image, ImageDraw, ImageFont

CARD_SIZE = 1080

GREEN = (21, 128, 61)
LIGHT_GREEN = (234, 243, 222)
DARK_GREEN = (23, 52, 4)
MID_GREEN = (39, 80, 10)
GRAY_BG = (241, 239, 232)
DARK = (17, 24, 39)
GRAY_TEXT = (107, 114, 128)
WHITE = (255, 255, 255)

FONT_PATH = str(settings.BASE_DIR / 'static' / 'fonts' / 'NotoSansBengali-Regular.ttf')

_FONT_CACHE = {}


def _font(size):
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = ImageFont.truetype(FONT_PATH, size, layout_engine=ImageFont.Layout.RAQM)
    return _FONT_CACHE[size]


def _text(draw, xy, text, size, fill, anchor='la'):
    draw.text(xy, text, font=_font(size), fill=fill, anchor=anchor)


def _text_width(text, size):
    return _font(size).getlength(text)


_LOGO_CACHE = None


def _get_logo():
    global _LOGO_CACHE
    if _LOGO_CACHE is None:
        path = finders.find('img/logo_transparent.png')
        _LOGO_CACHE = Image.open(path).convert('RGBA') if path else False
    return _LOGO_CACHE or None


def _fmt_amount(value):
    return f"৳{value:,.0f}"


def generate_share_card(donation, show_amount=False):
    """
    donation: a verified Donation instance (select_related('campaign') recommended).
    show_amount: whether to show this donor's own amount — off by default,
        since publicly broadcasting exactly how much someone gave can feel
        exposing; the campaign-wide progress is shown either way.
    Returns a BytesIO of a PNG, ready to stream straight back in a response.
    """
    campaign = donation.campaign
    img = Image.new('RGB', (CARD_SIZE, CARD_SIZE), WHITE)
    draw = ImageDraw.Draw(img)

    # ── HEADER ──
    header_h = 460
    draw.rectangle([0, 0, CARD_SIZE, header_h], fill=GREEN)

    logo = _get_logo()
    if logo:
        logo_h = 56
        ratio = logo_h / logo.height
        logo_resized = logo.resize((int(logo.width * ratio), logo_h))
        logo_x = CARD_SIZE // 2 - logo_resized.width // 2 - 18
        img.paste(logo_resized, (logo_x, 56), logo_resized)
        _text(draw, (logo_x + logo_resized.width + 12, 56 + logo_h // 2), "সহায়.bd", 40, WHITE, anchor='lm')
    else:
        _text(draw, (CARD_SIZE // 2, 56 + 28), "সহায়.bd", 44, WHITE, anchor='mm')

    # White checkmark circle
    circle_r = 72
    circle_cy = 230
    draw.ellipse(
        [CARD_SIZE // 2 - circle_r, circle_cy - circle_r, CARD_SIZE // 2 + circle_r, circle_cy + circle_r],
        fill=WHITE,
    )
    check_font = _font(90)
    cx, cy = CARD_SIZE // 2, circle_cy
    draw.line([(cx - 32, cy + 2), (cx - 8, cy + 26), (cx + 34, cy - 28)], fill=GREEN, width=14, joint='curve')

    headline = f"{donation.display_name} দান করেছেন"
    _text(draw, (CARD_SIZE // 2, 340), headline, 46, WHITE, anchor='mm')

    # ── BODY ──
    pad = 60
    card_top = header_h - 40
    card_h = 220

    # Campaign name card
    draw.rounded_rectangle(
        [pad, card_top, CARD_SIZE - pad, card_top + 110],
        radius=20, fill=WHITE, outline=(229, 231, 235), width=2,
    )
    _text(draw, (pad + 32, card_top + 26), "ক্যাম্পেইন", 24, GRAY_TEXT)
    title = campaign.title
    max_w = CARD_SIZE - 2 * pad - 64
    while _text_width(title, 34) > max_w and len(title) > 10:
        title = title[:-2]
    if title != campaign.title:
        title += '…'
    _text(draw, (pad + 32, card_top + 58), title, 34, DARK)

    # Stat boxes: raised / target
    stats_top = card_top + 130
    stat_h = 130
    gap = 24
    stat_w = (CARD_SIZE - 2 * pad - gap) // 2

    draw.rounded_rectangle(
        [pad, stats_top, pad + stat_w, stats_top + stat_h],
        radius=18, fill=LIGHT_GREEN,
    )
    _text(draw, (pad + 28, stats_top + 24), "সংগ্রহ হয়েছে", 22, MID_GREEN)
    _text(draw, (pad + 28, stats_top + 58), _fmt_amount(campaign.raised_amount), 38, DARK_GREEN)

    x2 = pad + stat_w + gap
    draw.rounded_rectangle(
        [x2, stats_top, x2 + stat_w, stats_top + stat_h],
        radius=18, fill=GRAY_BG,
    )
    _text(draw, (x2 + 28, stats_top + 24), "লক্ষ্য", 22, GRAY_TEXT)
    _text(draw, (x2 + 28, stats_top + 58), _fmt_amount(campaign.target_amount), 38, DARK)

    if show_amount and donation.amount:
        badge_text = f"{donation.display_name}-এর অবদান: {_fmt_amount(donation.amount)}"
        badge_y = stats_top + stat_h + 24
        draw.rounded_rectangle(
            [pad, badge_y, CARD_SIZE - pad, badge_y + 64],
            radius=14, fill=LIGHT_GREEN,
        )
        _text(draw, (CARD_SIZE // 2, badge_y + 32), badge_text, 26, MID_GREEN, anchor='mm')
        progress_top = badge_y + 64 + 30
    else:
        progress_top = stats_top + stat_h + 40

    # Progress bar
    pct = 0
    if campaign.target_amount and campaign.target_amount > 0:
        pct = min(float(campaign.raised_amount) / float(campaign.target_amount), 1.0)
    bar_h = 20
    draw.rounded_rectangle(
        [pad, progress_top, CARD_SIZE - pad, progress_top + bar_h],
        radius=bar_h // 2, fill=GRAY_BG,
    )
    if pct > 0:
        fill_w = int((CARD_SIZE - 2 * pad) * pct)
        fill_w = max(fill_w, bar_h)  # keep the rounded cap from looking clipped at tiny %
        draw.rounded_rectangle(
            [pad, progress_top, pad + fill_w, progress_top + bar_h],
            radius=bar_h // 2, fill=(99, 153, 34),
        )

    # Emotional line (campaign's short pitch, if any — else a generic line)
    pitch = getattr(campaign, 'short_pitch', '') or 'আপনার সাহায্যে বদলে যেতে পারে একটা জীবন'
    pitch_top = progress_top + bar_h + 34
    _text(draw, (CARD_SIZE // 2, pitch_top), pitch, 26, GRAY_TEXT, anchor='mm')

    # Decorative heart row fills the remaining space between the pitch line
    # and the footer, so the card doesn't trail off into dead whitespace.
    deco_cy = (pitch_top + (CARD_SIZE - 110)) // 2 + 10
    heart_r = 7
    heart_gap = 30
    hearts = 3
    total_w = (hearts - 1) * heart_gap
    hx = CARD_SIZE // 2 - total_w / 2
    for i in range(hearts):
        draw.ellipse(
            [hx - heart_r, deco_cy - heart_r, hx + heart_r, deco_cy + heart_r],
            fill=LIGHT_GREEN, outline=(197, 224, 165), width=2,
        )
        hx += heart_gap

    # Footer: site link
    footer_top = CARD_SIZE - 110
    draw.rounded_rectangle(
        [pad, footer_top, CARD_SIZE - pad, footer_top + 66],
        radius=14, fill=GRAY_BG,
    )
    domain = getattr(settings, 'SITE_DOMAIN', 'sohay.pythonanywhere.com')
    text_w = _text_width(domain, 28)
    tri_gap = 14
    total_w = 18 + tri_gap + text_w
    start_x = CARD_SIZE // 2 - total_w / 2
    tri_cy = footer_top + 33
    draw.polygon(
        [(start_x, tri_cy - 9), (start_x, tri_cy + 9), (start_x + 16, tri_cy)],
        fill=MID_GREEN,
    )
    _text(draw, (start_x + 18 + tri_gap, tri_cy), domain, 28, MID_GREEN, anchor='lm')

    buf = BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf
