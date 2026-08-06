"""
SSLCommerz adapter — based on SSLCommerz's documented v4 API:
https://developer.sslcommerz.com/doc/v4/

To activate this gateway once you have real credentials from SSLCommerz:
    1. Set these in your .env / PythonAnywhere environment variables:
         ACTIVE_PAYMENT_GATEWAY=sslcommerz
         SSLCOMMERZ_STORE_ID=<your store id>
         SSLCOMMERZ_STORE_PASSWORD=<your store password>
         SSLCOMMERZ_SANDBOX=False        (True while testing)
    2. In your SSLCommerz merchant panel, set the IPN URL to:
         https://sohay.pythonanywhere.com/payments/ipn/sslcommerz/
    3. Reload the web app. Nothing else needs to change.

Until those are set, is_configured() returns False and the donate view
falls back to the manual flow automatically (see donations/views.py).
"""
import requests
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.urls import reverse

from .base import PaymentGateway


class SSLCommerzGateway(PaymentGateway):

    def _base_url(self):
        return 'https://sandbox.sslcommerz.com' if settings.SSLCOMMERZ_SANDBOX else 'https://securepay.sslcommerz.com'

    def is_configured(self):
        return bool(settings.SSLCOMMERZ_STORE_ID and settings.SSLCOMMERZ_STORE_PASSWORD)

    def initiate(self, donation, request):
        tran_id = donation.transaction_id.hex  # 32 chars, well under SSLCommerz's 30-char *display* norm but accepted

        payload = {
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
            'total_amount': str(donation.amount),
            'currency': 'BDT',
            'tran_id': tran_id,
            'product_category': 'donation',
            'product_name': 'Donation',
            'product_profile': 'general',
            'success_url': request.build_absolute_uri(reverse('payment_success', args=['sslcommerz'])),
            'fail_url': request.build_absolute_uri(reverse('payment_fail', args=['sslcommerz'])),
            'cancel_url': request.build_absolute_uri(reverse('payment_cancel', args=['sslcommerz'])),
            'ipn_url': request.build_absolute_uri(reverse('payment_ipn', args=['sslcommerz'])),
            'shipping_method': 'NO',
            'cus_name': donation.donor_name or 'Anonymous Donor',
            'cus_email': donation.donor_email or 'no-reply@example.com',
            'cus_add1': 'Dhaka',
            'cus_city': 'Dhaka',
            'cus_postcode': '1000',
            'cus_country': 'Bangladesh',
            'cus_phone': donation.donor_phone or '01000000000',
        }

        try:
            resp = requests.post(f'{self._base_url()}/gwprocess/v4/api.php', data=payload, timeout=15)
            data = resp.json()
        except (requests.RequestException, ValueError):
            return {'mode': 'manual'}  # network/API hiccup — don't dead-end the donor, fall back

        if data.get('status') == 'SUCCESS' and data.get('GatewayPageURL'):
            return {'mode': 'redirect', 'url': data['GatewayPageURL']}
        return {'mode': 'manual'}  # API call failed — fall back rather than dead-end the donor

    def _validate(self, val_id):
        """Re-check a transaction server-to-server, as SSLCommerz's docs
        explicitly require, rather than trusting the redirect/IPN POST body
        alone (their docs: 'Due to security issue and to avoid data
        tampering, you must call the SSLCommerz APIs from your server')."""
        try:
            resp = requests.get(
                f'{self._base_url()}/validator/api/validationserverAPI.php',
                params={
                    'val_id': val_id,
                    'store_id': settings.SSLCOMMERZ_STORE_ID,
                    'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
                    'format': 'json',
                },
                timeout=15,
            )
            return resp.json()
        except Exception:
            return {}

    def handle_callback(self, request):
        import uuid
        from donations.models import Donation

        post = request.POST
        tran_id = post.get('tran_id', '')
        val_id = post.get('val_id', '')

        donation = None
        if tran_id:
            try:
                donation = Donation.objects.filter(transaction_id=uuid.UUID(tran_id)).first()
            except (ValueError, AttributeError):
                donation = None

        verified_ok = False
        verified_amount = None
        if val_id:
            check_data = self._validate(val_id)
            if check_data.get('status') in ('VALID', 'VALIDATED'):
                verified_ok = True
                try:
                    verified_amount = Decimal(check_data.get('amount', '0'))
                except (InvalidOperation, TypeError):
                    verified_amount = None

        # SECURITY: never fall back to trusting post['status'] alone — that
        # field arrives via a browser redirect and can be forged by anyone
        # who knows a donation's transaction_id. Only the server-to-server
        # _validate() call above (verified_ok) can be trusted.
        success = verified_ok

        return {
            'success': success,
            'donation': donation,
            'gateway_txn_id': post.get('bank_tran_id', val_id or tran_id),
            'amount': verified_amount,
            'raw': post.dict(),
        }
