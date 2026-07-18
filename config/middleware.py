"""
Custom middleware for the Sohay / SADKA project.
"""
import os
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Load the GeoIP2 country database once, at process start — not per-request.
# If the package or the database file isn't available for any reason, we
# degrade gracefully: everyone just gets the normal default language (bn),
# exactly like today, instead of the site breaking.
_GEOIP_READER = None
try:
    import geoip2.database

    _GEOIP_PATH = os.path.join(settings.BASE_DIR, 'geoip', 'GeoLite2-Country.mmdb')
    if os.path.exists(_GEOIP_PATH):
        _GEOIP_READER = geoip2.database.Reader(_GEOIP_PATH)
    else:
        logger.warning("GeoLite2-Country.mmdb not found at %s — geo-based default language is disabled.", _GEOIP_PATH)
except ImportError:
    logger.warning("geoip2 package not installed — geo-based default language is disabled.")


def _get_client_ip(request):
    """Real client IP, accounting for the reverse proxy PythonAnywhere (and
    most hosts) sit behind. X-Forwarded-For can contain a comma-separated
    chain (client, proxy1, proxy2, ...) — the first entry is the original client."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class GeoDefaultLanguageMiddleware:
    """
    Chooses a sensible *default* site language for first-time visitors,
    based on where their IP address is from:

      - Bangladesh (or the visitor's country can't be determined at all,
        e.g. local/private IPs during development) -> Bengali
      - Any other country -> English

    This only ever applies to visitors who have not yet made an explicit
    choice. As soon as someone taps the বাংলা/English button, Django's own
    language cookie remembers that choice, and this middleware backs off
    completely and never overrides it again — even on later visits.

    Must be placed in MIDDLEWARE *before* django.middleware.locale.LocaleMiddleware,
    so LocaleMiddleware sees the language this middleware selects.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cookie_name = settings.LANGUAGE_COOKIE_NAME
        has_explicit_choice = cookie_name in request.COOKIES
        detected_lang = None

        if not has_explicit_choice:
            detected_lang = self._detect_language(request)
            # Inject it into request.COOKIES so LocaleMiddleware (which runs
            # right after this middleware, per MIDDLEWARE order) treats it
            # exactly as if the browser had sent this cookie.
            request.COOKIES[cookie_name] = detected_lang

        response = self.get_response(request)

        if not has_explicit_choice and detected_lang:
            # Persist it as a real cookie too, so we only need to do the
            # GeoIP lookup once per visitor, not on every single request.
            response.set_cookie(
                cookie_name,
                detected_lang,
                max_age=365 * 24 * 60 * 60,
            )

        return response

    @staticmethod
    def _detect_language(request):
        if not _GEOIP_READER:
            return 'bn'

        ip = _get_client_ip(request)
        if not ip:
            return 'bn'

        try:
            result = _GEOIP_READER.country(ip)
            country_code = result.country.iso_code
        except Exception:
            # Local/private IPs (dev server), unknown addresses, bad input,
            # or any other lookup hiccup — fall back to the safe default.
            return 'bn'

        if country_code and country_code != 'BD':
            return 'en'
        return 'bn'
