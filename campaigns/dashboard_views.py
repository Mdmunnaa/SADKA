from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from campaigns.models import Campaign
from donations.models import Donation


@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Today's stats
    today_donations = Donation.objects.filter(created_at__date=today, is_verified=True)
    today_total = today_donations.aggregate(t=Sum('amount'))['t'] or 0
    today_count = today_donations.count()

    # Pending verification
    pending = Donation.objects.filter(is_verified=False)
    pending_count = pending.count()
    pending_total = pending.aggregate(t=Sum('amount'))['t'] or 0

    # All-time stats
    all_verified = Donation.objects.filter(is_verified=True)
    all_total = all_verified.aggregate(t=Sum('amount'))['t'] or 0
    all_donor_count = all_verified.count()

    # This week
    week_donations = Donation.objects.filter(created_at__date__gte=week_ago, is_verified=True)
    week_total = week_donations.aggregate(t=Sum('amount'))['t'] or 0

    # Top campaigns by amount raised
    top_campaigns = Campaign.objects.exclude(status='paused').order_by('-raised_amount')[:5]

    # Campaign status breakdown
    campaign_stats = {
        'urgent': Campaign.objects.filter(status='urgent').count(),
        'active': Campaign.objects.filter(status='active').count(),
        'completed': Campaign.objects.filter(status='completed').count(),
        'paused': Campaign.objects.filter(status='paused').count(),
    }

    # Recent pending donations (need action)
    recent_pending = pending.select_related('campaign').order_by('-created_at')[:10]

    # Recent verified donations
    recent_verified = all_verified.select_related('campaign').order_by('-created_at')[:10]

    context = {
        'today_total': today_total,
        'today_count': today_count,
        'pending_count': pending_count,
        'pending_total': pending_total,
        'all_total': all_total,
        'all_donor_count': all_donor_count,
        'week_total': week_total,
        'top_campaigns': top_campaigns,
        'campaign_stats': campaign_stats,
        'recent_pending': recent_pending,
        'recent_verified': recent_verified,
        'total_campaigns': Campaign.objects.exclude(status='paused').count(),
    }
    return render(request, 'dashboard/dashboard.html', context)
