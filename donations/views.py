from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from campaigns.models import Campaign
from .models import Donation, RecurringReminder


def donate(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)

    if request.method == 'POST':
        try:
            amount = request.POST.get('amount', '').strip()
            if not amount or float(amount) < 10:
                messages.error(request, 'সঠিক পরিমাণ দিন (সর্বনিম্ন ৳১০)।')
                return redirect('campaign_detail', slug=slug)

            donation = Donation.objects.create(
                campaign=campaign,
                donor_name=request.POST.get('donor_name', '').strip(),
                donor_phone=request.POST.get('donor_phone', '').strip(),
                donor_email=request.POST.get('donor_email', '').strip(),
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
