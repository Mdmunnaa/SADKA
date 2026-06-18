from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from .models import Campaign, Category


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


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

    # Dynamic SEO title/description based on active filters
    status_labels = {'urgent': 'জরুরি', 'active': 'চলমান', 'completed': 'সম্পন্ন'}
    selected_category_obj = Category.objects.filter(id=category_id).first() if category_id else None

    seo_parts = []
    if selected_category_obj:
        seo_parts.append(selected_category_obj.name)
    if status in status_labels:
        seo_parts.append(status_labels[status])
    if search:
        seo_parts.append(f'"{search}"')

    if seo_parts:
        seo_title = f"{' · '.join(seo_parts)} ক্যাম্পেইন — সহায়.bd"
        seo_description = f"{' ও '.join(seo_parts)} সম্পর্কিত ডোনেশন ক্যাম্পেইন দেখুন এবং সহায়তা করুন। সহায়.bd-তে বিকাশ/নগদে সহজে দান করুন।"
    else:
        seo_title = "সকল ক্যাম্পেইন — সহায়.bd"
        seo_description = "বাংলাদেশের অসহায় মানুষদের জন্য চলমান সকল ডোনেশন ক্যাম্পেইন দেখুন। চিকিৎসা, শিক্ষা, খাদ্য ও দুর্যোগ সহায়তায় আজই দান করুন।"

    # Pagination — 9 campaigns per page (matches 3-column grid nicely)
    paginator = Paginator(campaigns, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'campaigns': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': status,
        'search': search,
        'seo_title': seo_title,
        'seo_description': seo_description,
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
