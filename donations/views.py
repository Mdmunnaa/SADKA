from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from campaigns.models import Campaign
from .models import Donation
import json


def donate(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)

    if request.method == 'POST':
        try:
            amount = request.POST.get('amount')
            donor_name = request.POST.get('donor_name', '').strip()
            donor_phone = request.POST.get('donor_phone', '').strip()
            donor_email = request.POST.get('donor_email', '').strip()
            payment_method = request.POST.get('payment_method', 'bkash')
            payment_reference = request.POST.get('payment_reference', '').strip()
            is_anonymous = request.POST.get('is_anonymous') == 'on'
            message_text = request.POST.get('message', '').strip()

            if not amount or float(amount) <= 0:
                messages.error(request, 'সঠিক পরিমাণ দিন।')
                return redirect('donate', slug=slug)

            donation = Donation.objects.create(
                campaign=campaign,
                donor_name=donor_name,
                donor_phone=donor_phone,
                donor_email=donor_email,
                amount=amount,
                payment_method=payment_method,
                payment_reference=payment_reference,
                is_anonymous=is_anonymous,
                message=message_text,
                is_verified=False,
            )

            messages.success(request, f'আপনার ডোনেশন সফলভাবে জমা হয়েছে! আমরা শীঘ্রই যাচাই করবো।')
            return redirect('donation_success', pk=donation.pk)

        except Exception as e:
            messages.error(request, 'কিছু একটা ভুল হয়েছে। আবার চেষ্টা করুন।')
            return redirect('donate', slug=slug)

    context = {'campaign': campaign}
    return render(request, 'donations/donate.html', context)


def donation_success(request, pk):
    donation = get_object_or_404(Donation, pk=pk)
    return render(request, 'donations/success.html', {'donation': donation})


def donation_list(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)
    donors = campaign.donations.filter(is_verified=True).order_by('-created_at')
    return render(request, 'donations/list.html', {'campaign': campaign, 'donors': donors})
