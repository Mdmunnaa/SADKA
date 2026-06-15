from django.contrib import admin
from .models import Campaign, Category, CampaignUpdate


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']


class CampaignUpdateInline(admin.TabularInline):
    model = CampaignUpdate
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'target_amount', 'raised_amount', 'progress_percent', 'is_featured', 'created_at']
    list_filter = ['status', 'category', 'is_featured']
    search_fields = ['title', 'description']
    list_editable = ['status', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CampaignUpdateInline]
    readonly_fields = ['raised_amount', 'created_at', 'updated_at']

    fieldsets = (
        ('মূল তথ্য', {
            'fields': ('title', 'slug', 'category', 'status', 'is_featured')
        }),
        ('বিবরণ', {
            'fields': ('short_description', 'description', 'image', 'location')
        }),
        ('অর্থ সংক্রান্ত', {
            'fields': ('target_amount', 'raised_amount', 'deadline')
        }),
        ('পেমেন্ট নম্বর', {
            'fields': ('bkash_number', 'nagad_number', 'rocket_number')
        }),
    )
