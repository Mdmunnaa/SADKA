"""
aamarPay adapter — based on aamarPay's documented JSON API:
https://aamarpay.readme.io/reference/initiate-payment-json
https://aamarpay.readme.io/reference/search-transaction

To activate this gateway once you have real credentials from aamarPay:
    1. Set these in your .env / PythonAnywhere environment variables:
         ACTIVE_PAYMENT_GATEWAY=aamarpay
         AAMARPAY_STORE_ID=<your store id>
         AAMARPAY_SIGNATURE_KEY=<your signature key>
         AAMARPAY_SANDBOX=False        (True while testing)
    2. Reload the web app. Nothing else needs to change — donations/views.py
       and the donate modal already branch on ACTIVE_PAYMENT_GATEWAY.

Until those are set, is_configured() returns False and the donate view
falls back to the manual flow automatically (see donations/views.py).
"""
import requests
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.urls import reverse

from .base import PaymentGateway


class AamarPayGateway(PaymentGateway):

    def _base_url(self):
        return 'https://sandbox.aamarpay.com' if settings.AAMARPAY_SANDBOX else 'https://secure.aamarpay.com'

    def is_configured(self):
        return bool(settings.AAMARPAY_STORE_ID and settings.AAMARPAY_SIGNATURE_KEY)

    def initiate(self, donation, request):
        tran_id = donation.transaction_id.hex  # 32 chars, fits aamarPay's 32-char max

        payload = {
            'store_id': settings.AAMARPAY_STORE_ID,
            'signature_key': settings.AAMARPAY_SIGNATURE_KEY,
            'tran_id': tran_id,
            'amount': str(donation.amount),
            'currency': 'BDT',
            'desc': f"Donation to {donation.campaign.title}"[:255],
            'cus_name': donation.donor_name or 'Anonymous Donor',
            'cus_email': donation.donor_email or 'no-reply@example.com',
            'cus_phone': donation.donor_phone or '01000000000',
            'cus_add1': 'Bangladesh',
            'cus_country': 'Bangladesh',
            'success_url': request.build_absolute_uri(reverse('payment_success', args=['aamarpay'])),
            'fail_url': request.build_absolute_uri(reverse('payment_fail', args=['aamarpay'])),
            'cancel_url': request.build_absolute_uri(reverse('payment_cancel', args=['aamarpay'])),
            'type': 'json',
        }

        try:
            resp = requests.post(f'{self._base_url()}/jsonpost.php', json=payload, timeout=15)
            data = resp.json()
        except (requests.RequestException, ValueError):
            return {'mode': 'manual'}  # network/API hiccup — don't dead-end the donor, fall back

        if data.get('result') == 'true' and data.get('payment_url'):
            return {'mode': 'redirect', 'url': data['payment_url']}
        return {'mode': 'manual'}  # API call failed — fall back rather than dead-end the donor

    def handle_callback(self, request):
        import uuid
        from donations.models import Donation

        # aamarPay POSTs the full transaction result to success_url/fail_url.
        post = request.POST
        tran_id = post.get('mer_txnid', '')
        pay_status = post.get('pay_status', '')

        donation = None
        if tran_id:
            try:
                donation = Donation.objects.filter(transaction_id=uuid.UUID(tran_id)).first()
            except (ValueError, AttributeError):
                donation = None

        # Defense-in-depth: aamarPay explicitly recommends re-checking via
        # the Search Transaction API rather than trusting the redirect POST
        # alone (that POST could in theory be replayed/forged by a visitor's
        # own browser, since success_url is also a browser redirect target,
        # not only a server-to-server webhook).
        verified_ok = False
        verified_amount = None
        if tran_id:
            try:
                check = requests.get(
                    f'{self._base_url()}/api/v1/trxcheck/request.php',
                    params={
                        'request_id': tran_id,
                        'store_id': settings.AAMARPAY_STORE_ID,
                        'signature_key': settings.AAMARPAY_SIGNATURE_KEY,
                        'type': 'json',
                    },
                    timeout=15,
                )
                check_data = check.json()
                if check_data.get('status_code') == '2':  # 2 = Successful
                    verified_ok = True
                    try:
                        verified_amount = Decimal(check_data.get('amount', '0'))
                    except (InvalidOperation, TypeError):
                        verified_amount = None
            except Exception:
                pass

        # SECURITY: never fall back to trusting pay_status alone — that
        # field arrives via a browser redirect and can be forged by anyone
        # who knows a donation's transaction_id. Only the server-to-server
        # Search Transaction API call above (verified_ok) can be trusted.
        success = verified_ok

        return {
            'success': success,
            'donation': donation,
            'gateway_txn_id': post.get('pg_txnid', tran_id),
            'amount': verified_amount,
            'raw': post.dict(),
        }
