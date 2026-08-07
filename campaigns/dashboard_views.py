from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
from campaigns.models import Campaign
from donations.models import Donation
from campaigns.audit_report import generate_audit_report_pdf, generate_audit_report_csv


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


def _parse_date(value):
    """'YYYY-MM-DD' from a <input type=date> -> date object, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@staff_member_required
def audit_report(request):
    """
    Lets a logged-in admin pick a date range and one or more campaigns
    (or 'all'), then either shows the filter form (no params yet) or
    streams back a PDF audit report for exactly what was selected.
    Only verified donations are ever included — see the note printed
    at the bottom of the PDF itself.
    """
    all_campaigns = Campaign.objects.order_by('title')

    # No filters submitted yet -> just show the form.
    if 'generate' not in request.GET:
        return render(request, 'dashboard/audit_report_form.html', {
            'campaigns': all_campaigns,
        })

    date_from = _parse_date(request.GET.get('date_from', ''))
    date_to = _parse_date(request.GET.get('date_to', ''))
    selected_ids = request.GET.getlist('campaign')  # empty list == "all campaigns"

    donations = Donation.objects.filter(is_verified=True).select_related('campaign')
    if date_from:
        donations = donations.filter(created_at__date__gte=date_from)
    if date_to:
        donations = donations.filter(created_at__date__lte=date_to)
    if selected_ids:
        donations = donations.filter(campaign_id__in=selected_ids)

    if selected_ids:
        names = list(all_campaigns.filter(id__in=selected_ids).values_list('title', flat=True))
        campaign_filter_label = ', '.join(names) if len(names) <= 3 else f"{len(names)}টি নির্বাচিত ক্যাম্পেইন"
    else:
        campaign_filter_label = 'সব ক্যাম্পেইন'

    generated_by = request.user.get_full_name() or request.user.username

    if request.GET.get('format') == 'csv':
        csv_buf = generate_audit_report_csv(donations, date_from, date_to)
        filename = f"sahay-audit-report-{timezone.now().strftime('%Y%m%d-%H%M')}.csv"
        response = HttpResponse(csv_buf.read(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    pdf_buf = generate_audit_report_pdf(
        donations, date_from, date_to, campaign_filter_label, generated_by,
    )

    filename = f"sahay-audit-report-{timezone.now().strftime('%Y%m%d-%H%M')}.pdf"
    response = HttpResponse(pdf_buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
