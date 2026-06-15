from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Campaign, Category


def home(request):
    featured = Campaign.objects.filter(status__in=['active', 'urgent'], is_featured=True)[:3]
    urgent = Campaign.objects.filter(status='urgent').order_by('-created_at')[:4]
    active = Campaign.objects.filter(status='active').order_by('-created_at')[:6]
    completed = Campaign.objects.filter(status='completed').order_by('-created_at')[:3]
    categories = Category.objects.all()

    # Stats
    from donations.models import Donation
    from django.db.models import Sum, Count
    stats = {
        'total_raised': Donation.objects.filter(is_verified=True).aggregate(t=Sum('amount'))['t'] or 0,
        'total_donors': Donation.objects.filter(is_verified=True).count(),
        'total_campaigns': Campaign.objects.exclude(status='paused').count(),
        'completed_campaigns': Campaign.objects.filter(status='completed').count(),
    }

    context = {
        'featured': featured,
        'urgent': urgent,
        'active': active,
        'completed': completed,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'campaigns/home.html', context)


def campaign_list(request):
    campaigns = Campaign.objects.exclude(status='paused')
    categories = Category.objects.all()

    # Filter
    category_id = request.GET.get('category')
    status = request.GET.get('status')
    search = request.GET.get('q')

    if category_id:
        campaigns = campaigns.filter(category_id=category_id)
    if status:
        campaigns = campaigns.filter(status=status)
    if search:
        campaigns = campaigns.filter(Q(title__icontains=search) | Q(description__icontains=search))

    context = {
        'campaigns': campaigns,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': status,
        'search': search,
    }
    return render(request, 'campaigns/list.html', context)


def campaign_detail(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)
    updates = campaign.updates.all()
    recent_donors = campaign.donations.filter(is_verified=True).order_by('-created_at')[:10]
    related = Campaign.objects.filter(
        category=campaign.category, status__in=['active', 'urgent']
    ).exclude(pk=campaign.pk)[:3]

    context = {
        'campaign': campaign,
        'updates': updates,
        'recent_donors': recent_donors,
        'related': related,
    }
    return render(request, 'campaigns/detail.html', context)
