"""
Lightweight, dependency-free spam protection for public-facing forms
(donation, volunteer signup, comments) — no external CAPTCHA service to
sign up for, no extra JS library to load, just three well-established,
low-friction techniques stacked together:

1. Honeypot field — an input real visitors never see (hidden off-screen
   with CSS) or fill in. Most unsophisticated bots fill in every field
   they find in the HTML, so a filled honeypot is a near-certain bot signal.

2. Timing check — a hidden timestamp set when the form is first rendered.
   Real people take at least a couple of seconds to read a form and type
   into it; a submission that arrives faster than that almost always means
   a script fetched the page and posted straight back without "reading" it.

3. Per-IP rate limiting — even a bot that clears both checks above can't
   flood a form hundreds of times per minute from the same address.

None of this ever shows a real visitor a puzzle, a checkbox, or any extra
step — it's all invisible when a human fills the form out normally.
"""
import time

from django.core.cache import cache

from .security_utils import get_client_ip

HONEYPOT_FIELD = 'website_url'
TIMESTAMP_FIELD = 'form_rendered_at'
MIN_SUBMIT_SECONDS = 2


def form_timestamp():
    """Call when rendering a GET page that contains a protected form, and
    put the result in a hidden input named TIMESTAMP_FIELD in that form."""
    return str(int(time.time()))


def is_bot_submission(request):
    """True if this POST looks automated: the honeypot field was filled in,
    or it arrived faster than any real person could have filled the form."""
    if request.POST.get(HONEYPOT_FIELD, '').strip():
        return True
    try:
        rendered_at = int(request.POST.get(TIMESTAMP_FIELD, '0'))
    except (TypeError, ValueError):
        return True  # missing/tampered timestamp is itself suspicious
    if time.time() - rendered_at < MIN_SUBMIT_SECONDS:
        return True
    return False


def is_rate_limited(request, key_prefix, limit=5, window_seconds=600):
    """True if this IP has already made `limit`-or-more submissions to this
    particular form within the last `window_seconds`. Built on Django's
    cache framework, so it works with the default in-process cache with no
    extra setup, and keeps working transparently if the site later moves
    to Redis/Memcached for caching."""
    ip = get_client_ip(request) or 'unknown'
    cache_key = f"ratelimit:{key_prefix}:{ip}"
    count = cache.get(cache_key, 0)
    if count >= limit:
        return True
    cache.set(cache_key, count + 1, timeout=window_seconds)
    return False
