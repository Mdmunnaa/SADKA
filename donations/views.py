from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from campaigns.models import Campaign
from .models import Donation, RecurringReminder
from config.spam_protection import is_bot_submission, is_rate_limited
from .gateways import get_active_gateway, get_gateway_by_name


def donate(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)

    if request.method == 'POST':
        if is_bot_submission(request):
            return redirect('campaign_detail', slug=slug)
        if is_rate_limited(request, 'donate', limit=8, window_seconds=600):
            messages.error(request, 'একটু পর আবার চেষ্টা করুন — অনেকগুলো অনুরোধ একসাথে জমা হয়েছে।')
            return redirect('campaign_detail', slug=slug)

        try:
            amount = request.POST.get('amount', '').strip()
            if not amount or float(amount) < 10:
                messages.error(request, 'সঠিক পরিমাণ দিন (সর্বনিম্ন ৳১০)।')
                return redirect('campaign_detail', slug=slug)

            donation = Donation.objects.create(
                campaign=campaign,
                donor_name=request.POST.get('donor_name', '').strip() or (request.user.get_full_name() if request.user.is_authenticated else ''),
                donor_phone=request.POST.get('donor_phone', '').strip() or (getattr(request.user, 'donor_profile', None) and request.user.donor_profile.phone or ''),
                donor_email=request.POST.get('donor_email', '').strip() or (request.user.email if request.user.is_authenticated else ''),
                amount=amount,
                payment_method=request.POST.get('payment_method', 'bkash'),
                payment_reference=request.POST.get('payment_reference', '').strip(),
                is_anonymous=request.POST.get('is_anonymous') == 'on',
                message=request.POST.get('message', '').strip(),
                is_verified=False,
            )

            # If user opted in for recurring reminder
            if request.POST.get('want_recurring') == 'on':
                RecurringReminder.objects.create(
                    campaign=campaign,
                    name=donation.donor_name,
                    phone=donation.donor_phone,
                    email=donation.donor_email,
                    amount=amount,
                    frequency=request.POST.get('recurring_frequency', 'monthly'),
                    is_active=True,
                )

            # ── Payment gateway branch ──
            # Default ('manual', no credentials configured): unchanged —
            # donor already typed their own reference above, just show the
            # thank-you/receipt page. Only takes a different path once a
            # real gateway is configured (see donations/gateways/).
            gateway = get_active_gateway()
            result = gateway.initiate(donation, request)
            if result.get('mode') == 'redirect':
                return redirect(result['url'])

            return redirect('donation_success', pk=donation.pk)

        except Exception:
            messages.error(request, 'কিছু একটা ভুল হয়েছে। আবার চেষ্টা করুন।')
            return redirect('campaign_detail', slug=slug)

    return redirect('campaign_detail', slug=slug)


def donation_success(request, pk):
    donation = get_object_or_404(Donation, pk=pk)
    return render(request, 'donations/success.html', {'donation': donation})


def recurring_signup(request):
    """Standalone page for setting up a recurring sadaqah reminder (not tied to one donation)."""
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            amount = request.POST.get('amount', '').strip()

            if not phone and not email:
                messages.error(request, 'ফোন নম্বর বা ইমেইল অবশ্যই দিতে হবে।')
                return redirect('recurring_signup')
            if not amount or float(amount) < 10:
                messages.error(request, 'সঠিক পরিমাণ দিন (সর্বনিম্ন ৳১০)।')
                return redirect('recurring_signup')

            campaign_id = request.POST.get('campaign')
            campaign = Campaign.objects.filter(id=campaign_id).first() if campaign_id else None

            RecurringReminder.objects.create(
                campaign=campaign,
                name=request.POST.get('name', '').strip(),
                phone=phone,
                email=email,
                amount=amount,
                frequency=request.POST.get('frequency', 'monthly'),
                is_active=True,
            )
            messages.success(request, 'আপনার রিকারিং সদকা রিমাইন্ডার সফলভাবে সেট করা হয়েছে! জাযাকাল্লাহ খায়রান।')
            return redirect('recurring_signup')
        except Exception:
            messages.error(request, 'কিছু একটা ভুল হয়েছে। আবার চেষ্টা করুন।')
            return redirect('recurring_signup')

    campaigns = Campaign.objects.exclude(status__in=['paused', 'completed'])
    return render(request, 'donations/recurring_signup.html', {'campaigns': campaigns})


# ── Payment gateway callbacks ──
# Only ever reached once a real gateway (aamarpay/sslcommerz) is actually
# configured and a donor was redirected there — irrelevant while
# ACTIVE_PAYMENT_GATEWAY stays at its default 'manual' value.

@csrf_exempt
def payment_success(request, gateway_name):
    gateway = get_gateway_by_name(gateway_name)
    if not gateway:
        return redirect('home')

    result = gateway.handle_callback(request)
    donation = result.get('donation')

    if result.get('success') and donation:
        donation.is_verified = True
        if result.get('gateway_txn_id'):
            donation.payment_reference = result['gateway_txn_id']
        donation.save()
        return redirect('donation_success', pk=donation.pk)

    if donation:
        messages.error(request, 'পেমেন্ট নিশ্চিত করা যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন অথবা আমাদের সাথে যোগাযোগ করুন।')
        return redirect('campaign_detail', slug=donation.campaign.slug)

    messages.error(request, 'পেমেন্ট নিশ্চিত করা যায়নি।')
    return redirect('home')


@csrf_exempt
def payment_fail(request, gateway_name):
    gateway = get_gateway_by_name(gateway_name)
    if not gateway:
        return redirect('home')

    result = gateway.handle_callback(request)
    donation = result.get('donation')

    messages.error(request, 'দুঃখিত, পেমেন্টটি সম্পন্ন হয়নি। অনুগ্রহ করে আবার চেষ্টা করুন।')
    if donation:
        return redirect('campaign_detail', slug=donation.campaign.slug)
    return redirect('home')


@csrf_exempt
def payment_cancel(request, gateway_name):
    gateway = get_gateway_by_name(gateway_name)
    if not gateway:
        return redirect('home')

    result = gateway.handle_callback(request)
    donation = result.get('donation')

    messages.info(request, 'পেমেন্ট বাতিল করা হয়েছে।')
    if donation:
        return redirect('campaign_detail', slug=donation.campaign.slug)
    return redirect('home')


@csrf_exempt
def payment_ipn(request, gateway_name):
    """Server-to-server notification (used by SSLCommerz especially) —
    the reliable confirmation channel that still works even if the donor
    closes their browser tab right after paying, before success_url's
    redirect finishes loading. Returns plain text, not a page — no browser
    is on the other end."""
    gateway = get_gateway_by_name(gateway_name)
    if not gateway:
        return HttpResponse('unknown gateway', status=404)

    result = gateway.handle_callback(request)
    donation = result.get('donation')

    if result.get('success') and donation and not donation.is_verified:
        donation.is_verified = True
        if result.get('gateway_txn_id'):
            donation.payment_reference = result['gateway_txn_id']
        donation.save()

    return HttpResponse('OK')
