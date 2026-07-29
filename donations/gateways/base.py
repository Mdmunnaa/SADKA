"""
Payment gateway abstraction layer.

The goal: the rest of the codebase (views, templates) never needs to know
*which* gateway is active. Switching from today's manual bKash/Nagad/Rocket
flow to an automated gateway (aamarPay, SSLCommerz, ...) later should be a
settings + API-credentials change — not a rewrite of donations/views.py or
the donate modal.

How it works:
    - `ACTIVE_PAYMENT_GATEWAY` in settings picks which adapter is "live"
      (default: 'manual' — today's behavior, unchanged).
    - `get_active_gateway()` below returns an instance of that adapter.
    - Every adapter implements the same three methods (see PaymentGateway),
      so donations/views.py just calls those methods without caring which
      concrete class it got back.

Adding a new gateway later: create a new file in this package implementing
PaymentGateway, register it in the GATEWAYS dict in __init__.py, and add its
credential settings — nothing else in the project needs to change.
"""
from abc import ABC, abstractmethod


class PaymentGateway(ABC):

    @abstractmethod
    def is_configured(self):
        """True if this gateway has everything it needs (API keys etc.) to
        actually run. Lets the donate view fall back safely to the manual
        flow if someone flips ACTIVE_PAYMENT_GATEWAY before adding keys."""
        ...

    @abstractmethod
    def initiate(self, donation, request):
        """
        Start payment for an already-created (but not yet verified) Donation.

        Returns a dict, one of:
          {'mode': 'redirect', 'url': <str>}
              — send the donor's browser to this URL (the gateway's own
              hosted checkout page) to complete payment.
          {'mode': 'manual'}
              — this gateway doesn't do redirects; use the existing on-site
              "send money to this number, then enter your reference" flow.
              This is always what ManualGateway returns.
        """
        ...

    @abstractmethod
    def handle_callback(self, request):
        """
        Parse the gateway's redirect/webhook back to our site after a
        payment attempt (success, fail, or cancel).

        Returns a dict:
          {'success': bool, 'donation': Donation|None,
           'gateway_txn_id': str, 'amount': Decimal|None, 'raw': dict}

        The calling view uses this to mark the Donation verified (or not)
        and show the right page — it never parses gateway-specific
        field names itself.
        """
        ...
