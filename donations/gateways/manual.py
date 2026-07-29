from .base import PaymentGateway


class ManualGateway(PaymentGateway):
    """
    Today's live flow, unchanged: the donor sends money themselves to a
    displayed bKash/Nagad/Rocket number and types in the Transaction
    ID/Reference on our site; an admin checks it against the real
    mobile-banking statement before marking the donation verified in the
    Django admin. No API calls, no credentials, nothing to configure —
    this is the safe default and always available.
    """

    def is_configured(self):
        return True

    def initiate(self, donation, request):
        return {'mode': 'manual'}

    def handle_callback(self, request):
        # The manual gateway has no redirect/webhook of its own —
        # verification happens by hand in the admin, not through this path.
        return {
            'success': False, 'donation': None,
            'gateway_txn_id': '', 'amount': None, 'raw': {},
        }
