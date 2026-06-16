from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from campaigns.models import Campaign
from .models import Donation


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
            return redirect('donation_success', pk=donation.pk)

        except Exception:
            messages.error(request, 'কিছু একটা ভুল হয়েছে। আবার চেষ্টা করুন।')
            return redirect('campaign_detail', slug=slug)

    return redirect('campaign_detail', slug=slug)


def donation_success(request, pk):
    donation = get_object_or_404(Donation, pk=pk)
    return render(request, 'donations/success.html', {'donation': donation})
