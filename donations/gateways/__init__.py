from django.conf import settings

from .manual import ManualGateway
from .aamarpay import AamarPayGateway
from .sslcommerz import SSLCommerzGateway

GATEWAYS = {
    'manual': ManualGateway,
    'aamarpay': AamarPayGateway,
    'sslcommerz': SSLCommerzGateway,
}


def get_active_gateway():
    """
    Returns an instance of whichever gateway is configured in settings
    (ACTIVE_PAYMENT_GATEWAY). Falls back to ManualGateway — today's live
    behavior — if the configured name is unknown or if it's not actually
    ready to use yet (e.g. 'aamarpay' selected but the API keys haven't
    been added). This means flipping the setting alone, before credentials
    exist, can never break the donate flow.
    """
    name = getattr(settings, 'ACTIVE_PAYMENT_GATEWAY', 'manual')
    gateway_cls = GATEWAYS.get(name, ManualGateway)
    gateway = gateway_cls()
    if not gateway.is_configured():
        return ManualGateway()
    return gateway


def get_gateway_by_name(name):
    """Used by the payment callback views, which receive the gateway name
    as part of the callback URL itself (e.g. /payments/success/aamarpay/)
    rather than reading it from settings — a stray old callback hitting the
    site after a gateway switch should still be handled by the gateway that
    actually issued it, not whatever is newly configured."""
    gateway_cls = GATEWAYS.get(name)
    return gateway_cls() if gateway_cls else None
