from django.contrib import admin
from django.db.models import Sum
from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'campaign', 'amount', 'payment_method', 'payment_reference', 'is_verified', 'is_anonymous', 'created_at']
    list_filter = ['is_verified', 'payment_method', 'campaign']
    search_fields = ['donor_name', 'donor_phone', 'payment_reference']
    list_editable = ['is_verified']
    readonly_fields = ['transaction_id', 'created_at']

    fieldsets = (
        ('ডোনার তথ্য', {
            'fields': ('donor_name', 'donor_phone', 'donor_email', 'is_anonymous', 'message')
        }),
        ('পেমেন্ট তথ্য', {
            'fields': ('campaign', 'amount', 'payment_method', 'payment_reference', 'is_verified')
        }),
        ('সিস্টেম', {
            'fields': ('transaction_id', 'created_at'),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Recalculate campaign raised amount
        from django.db.models import Sum
        campaign = obj.campaign
        total = Donation.objects.filter(
            campaign=campaign, is_verified=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        campaign.raised_amount = total
        campaign.save(update_fields=['raised_amount'])
