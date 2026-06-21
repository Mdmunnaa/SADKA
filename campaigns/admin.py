from django.contrib import admin
from django.utils.html import format_html
from .models import Campaign, Category, CampaignUpdate, Comment


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
    list_display = ['thumbnail', 'title', 'translation_status', 'category', 'status', 'target_amount', 'raised_amount', 'progress_percent', 'is_featured', 'created_at']
    list_display_links = ['title']
    list_filter = ['status', 'category', 'is_featured']
    search_fields = ['title', 'description']
    list_editable = ['status', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CampaignUpdateInline]
    readonly_fields = ['raised_amount', 'created_at', 'updated_at', 'image_preview_large']
    actions = ['translate_to_english']

    fieldsets = (
        ('মূল তথ্য', {
            'fields': ('title', 'slug', 'category', 'status', 'is_featured')
        }),
        ('বিবরণ', {
            'fields': ('short_description', 'description', 'image', 'image_preview_large', 'location')
        }),
        ('English Translation (স্বয়ংক্রিয়)', {
            'fields': ('title_en', 'short_description_en', 'description_en'),
            'classes': ('collapse',),
            'description': 'এই ফিল্ডগুলো "Translate to English" action দিয়ে স্বয়ংক্রিয়ভাবে পূরণ হয়। চাইলে সরাসরি এডিটও করতে পারবেন।'
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

    def translation_status(self, obj):
        if obj.title_en:
            return format_html('<span style="color:#15803d;font-weight:700;">✓ EN</span>')
        return format_html('<span style="color:#9ca3af;">— বাংলা শুধু</span>')
    translation_status.short_description = "অনুবাদ"

    def translate_to_english(self, request, queryset):
        success_count = 0
        fail_count = 0
        for campaign in queryset:
            if campaign.auto_translate_to_english():
                success_count += 1
            else:
                fail_count += 1

        if success_count:
            self.message_user(request, f"{success_count} টি ক্যাম্পেইন সফলভাবে English-এ অনুবাদ হয়েছে।")
        if fail_count:
            self.message_user(
                request,
                f"{fail_count} টি ক্যাম্পেইন অনুবাদ করা যায়নি (সম্ভবত ইন্টারনেট/translation সার্ভিস সমস্যা)। পরে আবার চেষ্টা করুন।",
                level='WARNING'
            )
    translate_to_english.short_description = "🌐 Translate selected campaigns to English"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign', 'message_short', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'campaign']
    search_fields = ['name', 'message']
    list_editable = ['is_approved']
    readonly_fields = ['created_at']

    def message_short(self, obj):
        return obj.message[:60] + ('...' if len(obj.message) > 60 else '')
    message_short.short_description = "মন্তব্য"


from .models import Volunteer

@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'profession', 'address_short', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'phone', 'nid', 'email']
    list_editable = ['status']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('ব্যক্তিগত তথ্য', {
            'fields': ('name', 'phone', 'email', 'profession', 'address', 'nid')
        }),
        ('আবেদন', {
            'fields': ('why_volunteer',)
        }),
        ('অ্যাডমিন সিদ্ধান্ত', {
            'fields': ('status', 'note', 'created_at')
        }),
    )

    def address_short(self, obj):
        return obj.address[:40] + '…' if len(obj.address) > 40 else obj.address
    address_short.short_description = 'ঠিকানা'
