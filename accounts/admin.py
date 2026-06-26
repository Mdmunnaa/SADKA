from django.contrib import admin
from .models import DonorProfile


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user_email', 'phone', 'total_donated', 'donation_count', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at', 'total_donated', 'donation_count']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'ইমেইল'

    def total_donated(self, obj):
        return f"৳{obj.total_donated}"
    total_donated.short_description = 'মোট দান'

    def donation_count(self, obj):
        return obj.donation_count
    donation_count.short_description = 'দানের সংখ্যা'
