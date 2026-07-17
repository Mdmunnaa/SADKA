from django.contrib import admin
from django.utils.html import format_html

from .models import BlogCategory, BlogTag, BlogPost, Comment


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    prepopulated_fields = {}  # slug is auto-generated in save() (Bengali-safe), not via JS
    search_fields = ('name',)

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'পোস্ট সংখ্যা'


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    search_fields = ('name',)

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'পোস্ট সংখ্যা'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status_badge', 'has_english_badge', 'category', 'author_name',
                    'related_campaign', 'published_at', 'views_count')
    list_filter = ('status', 'category', 'tags')
    search_fields = ('title', 'title_en', 'excerpt', 'content')
    autocomplete_fields = ('related_campaign',)
    filter_horizontal = ('tags',)
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'image_preview')
    date_hierarchy = 'published_at'
    actions = ['translate_to_english']

    fieldsets = (
        ('বিষয়বস্তু (বাংলা)', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image', 'image_preview')
        }),
        ('English Version', {
            'fields': ('title_en', 'excerpt_en', 'content_en'),
            'description': 'নিচে সিলেক্ট করে "Translate to English" action চালালে এই ফিল্ডগুলো স্বয়ংক্রিয়ভাবে ভরে যাবে। '
                           'তারপর চাইলে হাতে ঠিক করে নিতে পারেন। খালি রাখলে English mode-এও বাংলা কন্টেন্টই দেখাবে।',
        }),
        ('সংগঠন', {
            'fields': ('category', 'tags', 'author_name')
        }),
        ('প্রকাশনা', {
            'fields': ('status', 'published_at')
        }),
        ('ফান্ডরেইজিং লিংক', {
            'fields': ('related_campaign',),
            'description': 'এই পোস্টের Donate বাটনগুলো কোন ক্যাম্পেইনের দিকে যাবে সেটা এখানে বেছে দিন।'
        }),
        ('SEO (ঐচ্ছিক)', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('তথ্য', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colors = {'draft': '#6b7280', 'published': '#15803d', 'scheduled': '#b45309'}
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;">{}</span>',
            colors.get(obj.status, '#6b7280'), obj.get_status_display()
        )
    status_badge.short_description = 'অবস্থা'

    def has_english_badge(self, obj):
        if obj.title_en:
            return format_html('<span style="color:#15803d;">✓ EN</span>')
        return format_html('<span style="color:#9ca3af;">— EN</span>')
    has_english_badge.short_description = 'English?'

    def image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-width:300px;border-radius:8px;" />', obj.featured_image.url)
        return "(কোনো ছবি নেই)"
    image_preview.short_description = 'প্রিভিউ'

    def translate_to_english(self, request, queryset):
        success_count = 0
        fail_count = 0
        for post in queryset:
            if post.auto_translate_to_english():
                success_count += 1
            else:
                fail_count += 1

        if success_count:
            self.message_user(request, f"{success_count} টি পোস্ট সফলভাবে English-এ অনুবাদ হয়েছে।")
        if fail_count:
            self.message_user(
                request,
                f"{fail_count} টি পোস্ট অনুবাদ করা যায়নি (সম্ভবত ইন্টারনেট/translation সার্ভিস সমস্যা)। পরে আবার চেষ্টা করুন।",
                level='WARNING'
            )
    translate_to_english.short_description = "🌐 Translate selected posts to English"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('commenter_name', 'post', 'short_content', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'user__username', 'user__email', 'post__title')
    list_editable = ('is_approved',)
    autocomplete_fields = ('post', 'user')

    def short_content(self, obj):
        return obj.content[:60] + ('...' if len(obj.content) > 60 else '')
    short_content.short_description = 'মন্তব্য'
