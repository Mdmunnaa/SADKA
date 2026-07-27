"""
Small shared helpers used by more than one part of config/ (middleware,
spam protection, etc.) — kept here so neither has to duplicate the other's
logic.
"""


def get_client_ip(request):
    """Real client IP, accounting for the reverse proxy PythonAnywhere (and
    most hosts) sit behind. X-Forwarded-For can contain a comma-separated
    chain (client, proxy1, proxy2, ...) — the first entry is the original
    client."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
