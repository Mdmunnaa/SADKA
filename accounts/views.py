from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import DonorProfile
from donations.models import Donation


# ══ REGISTER ══
def donor_register(request):
    if request.user.is_authenticated:
        return redirect('donor_dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip().lower()
        phone      = request.POST.get('phone', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        # Validation
        if not all([first_name, email, password1]):
            messages.error(request, 'নাম, ইমেইল এবং পাসওয়ার্ড দেওয়া বাধ্যতামূলক।')
            return render(request, 'accounts/register.html', {'form_data': request.POST})

        if password1 != password2:
            messages.error(request, 'পাসওয়ার্ড দুটো মিলছে না।')
            return render(request, 'accounts/register.html', {'form_data': request.POST})

        if len(password1) < 6:
            messages.error(request, 'পাসওয়ার্ড কমপক্ষে ৬ অক্ষরের হতে হবে।')
            return render(request, 'accounts/register.html', {'form_data': request.POST})

        if User.objects.filter(email=email).exists():
            messages.error(request, 'এই ইমেইল দিয়ে আগেই একটি অ্যাকাউন্ট আছে।')
            return render(request, 'accounts/register.html', {'form_data': request.POST})

        # Create user
        username = email  # use email as username
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        DonorProfile.objects.create(user=user, phone=phone)

        # Auto login
        login(request, user)
        messages.success(request, f'স্বাগতম {first_name}! আপনার অ্যাকাউন্ট তৈরি হয়েছে।')
        next_url = request.GET.get('next', 'donor_dashboard')
        return redirect(next_url)

    return render(request, 'accounts/register.html')


# ══ LOGIN ══
def donor_login(request):
    if request.user.is_authenticated:
        return redirect('donor_dashboard')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'donor_dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'ইমেইল বা পাসওয়ার্ড ভুল।')

    return render(request, 'accounts/login.html', {
        'next': request.GET.get('next', ''),
    })


# ══ LOGOUT ══
def donor_logout(request):
    logout(request)
    messages.success(request, 'আপনি সফলভাবে লগআউট হয়েছেন।')
    return redirect('home')


# ══ DASHBOARD ══
@login_required(login_url='/accounts/login/')
def donor_dashboard(request):
    user = request.user
    profile, _ = DonorProfile.objects.get_or_create(user=user)

    # Match donations by email
    donations = Donation.objects.filter(
        donor_email=user.email
    ).select_related('campaign').order_by('-created_at')

    verified   = donations.filter(is_verified=True)
    pending    = donations.filter(is_verified=False)
    total_amount = verified.aggregate(t=Sum('amount'))['t'] or 0

    # Campaign-wise breakdown
    campaign_summary = {}
    for d in verified:
        cid = d.campaign_id
        if cid not in campaign_summary:
            campaign_summary[cid] = {
                'campaign': d.campaign,
                'total': 0,
                'count': 0,
            }
        campaign_summary[cid]['total'] += d.amount
        campaign_summary[cid]['count'] += 1

    context = {
        'profile': profile,
        'donations': donations[:20],
        'verified_count': verified.count(),
        'pending_count': pending.count(),
        'total_amount': total_amount,
        'campaign_summary': list(campaign_summary.values()),
    }
    return render(request, 'accounts/dashboard.html', context)


# ══ PROFILE EDIT ══
@login_required(login_url='/accounts/login/')
def donor_profile_edit(request):
    user = request.user
    profile, _ = DonorProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name', '').strip()
        user.save()

        profile.phone   = request.POST.get('phone', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.save()

        messages.success(request, 'প্রোফাইল আপডেট হয়েছে।')
        return redirect('donor_dashboard')

    return render(request, 'accounts/profile_edit.html', {
        'profile': profile,
    })


# ══ PDF RECEIPT ══
@login_required(login_url='/accounts/login/')
def donation_receipt(request, pk):
    from django.http import HttpResponse, Http404
    from .receipt import generate_receipt_pdf

    try:
        donation = Donation.objects.get(pk=pk, is_verified=True)
    except Donation.DoesNotExist:
        raise Http404

    # Security: only the donor who submitted (by email) can download
    if donation.donor_email and donation.donor_email != request.user.email:
        raise Http404

    buf = generate_receipt_pdf(donation)
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="sahay-receipt-{pk:06d}.pdf"'
    )
    return response
