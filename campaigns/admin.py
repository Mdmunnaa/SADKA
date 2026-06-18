from django.contrib import admin
from django.utils.html import format_html
from .models import Campaign, Category, CampaignUpdate


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']


class CampaignUpdateInline(admin.TabularInline):
    model = CampaignUpdate
    extra = 1
    fields = ['title', 'content', 'image', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;object-fit:cover;" />', obj.image.url)
        return "—"
    image_preview.short_description = "প্রিভিউ"


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['thumbnail', 'title', 'category', 'status', 'target_amount', 'raised_amount', 'progress_percent', 'is_featured', 'created_at']
    list_display_links = ['title']
    list_filter = ['status', 'category', 'is_featured']
    search_fields = ['title', 'description']
    list_editable = ['status', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CampaignUpdateInline]
    readonly_fields = ['raised_amount', 'created_at', 'updated_at', 'image_preview_large']

    fieldsets = (
        ('মূল তথ্য', {
            'fields': ('title', 'slug', 'category', 'status', 'is_featured')
        }),
        ('বিবরণ', {
            'fields': ('short_description', 'description', 'image', 'image_preview_large', 'location')
        }),
        ('অর্থ সংক্রান্ত', {
            'fields': ('target_amount', 'raised_amount', 'deadline')
        }),
        ('পেমেন্ট নম্বর', {
            'fields': ('bkash_number', 'nagad_number', 'rocket_number')
        }),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:45px;width:70px;border-radius:6px;object-fit:cover;" />', obj.image.url)
        return format_html('<div style="height:45px;width:70px;border-radius:6px;background:#f3f4f6;display:flex;align-items:center;justify-content:center;color:#9ca3af;font-size:11px;">No Image</div>')
    thumbnail.short_description = "ছবি"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:220px;border-radius:10px;border:1px solid #d1d5db;" />', obj.image.url)
        return "এখনো কোনো ছবি আপলোড করা হয়নি"
    image_preview_large.short_description = "ছবির প্রিভিউ"
