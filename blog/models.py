import re

from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

from campaigns.models import unicode_safe_slugify, resize_image, Campaign


class BlogCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='নাম')
    slug = models.SlugField(unique=True, blank=True, max_length=150, allow_unicode=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = unicode_safe_slugify(self.name) or 'category'
            slug = base_slug
            counter = 1
            while BlogCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "ব্লগ ক্যাটাগরি"
        verbose_name_plural = "ব্লগ ক্যাটাগরিসমূহ"
        ordering = ['name']


class BlogTag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='নাম')
    slug = models.SlugField(unique=True, blank=True, max_length=80, allow_unicode=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = unicode_safe_slugify(self.name) or 'tag'
            slug = base_slug
            counter = 1
            while BlogTag.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "ট্যাগ"
        verbose_name_plural = "ট্যাগসমূহ"
        ordering = ['name']


class PublishedPostManager(models.Manager):
    """Returns only posts that should currently be visible to the public
    (status is 'published' AND published_at is not in the future)."""
    def get_queryset(self):
        return super().get_queryset().filter(
            status='published',
            published_at__lte=timezone.now(),
        )


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'খসড়া'),
        ('published', 'প্রকাশিত'),
        ('scheduled', 'নির্ধারিত সময়ে প্রকাশ হবে'),
    ]

    # ── Content ──
    title = models.CharField(max_length=255, verbose_name='শিরোনাম (বাংলা)')
    title_en = models.CharField(max_length=255, blank=True, verbose_name='Title (English)',
                                 help_text='ঐচ্ছিক — English ভার্সনে দেখাতে চাইলে দিন')
    slug = models.SlugField(unique=True, blank=True, max_length=255, allow_unicode=True)

    excerpt = models.CharField(max_length=300, verbose_name='সংক্ষিপ্ত বিবরণ',
                                help_text='লিস্টিং পেজ ও সার্চ ইঞ্জিনে (SEO) এই লেখাটি দেখাবে')
    content = CKEditor5Field('বিস্তারিত লেখা', config_name='extends')

    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name='কভার ছবি')

    # ── Organization ──
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='posts', verbose_name='ক্যাটাগরি')
    tags = models.ManyToManyField(BlogTag, blank=True, related_name='posts', verbose_name='ট্যাগসমূহ')
    author_name = models.CharField(max_length=100, default='সহায়.bd টিম', verbose_name='লেখক')

    # ── Publishing ──
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='অবস্থা')
    published_at = models.DateTimeField(
        null=True, blank=True, verbose_name='প্রকাশের সময়',
        help_text='ফাঁকা রাখলে, "প্রকাশিত" করে সেভ করার সময় এখনকার সময় বসে যাবে। ভবিষ্যতের কোনো সময় দিলে, সেই সময়ের আগে পোস্টটি সাইটে দেখাবে না।',
    )

    # ── Fundraising tie-in ──
    related_campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='blog_posts', verbose_name='সম্পর্কিত ক্যাম্পেইন',
        help_text='এই পোস্টের Donate বাটনগুলো এই ক্যাম্পেইনের দিকে নির্দেশ করবে (না দিলে, সবচেয়ে জরুরি/ফিচার্ড ক্যাম্পেইন দেখাবে)',
    )

    # ── SEO overrides (optional) ──
    meta_title = models.CharField(max_length=255, blank=True, verbose_name='Meta Title',
                                   help_text='ফাঁকা রাখলে পোস্টের শিরোনামই ব্যবহার হবে')
    meta_description = models.CharField(max_length=300, blank=True, verbose_name='Meta Description',
                                         help_text='ফাঁকা রাখলে সংক্ষিপ্ত বিবরণ ব্যবহার হবে')

    views_count = models.PositiveIntegerField(default=0, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedPostManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = unicode_safe_slugify(self.title) or 'post'
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Auto-stamp published_at the first time a post goes live, so editors
        # don't have to remember to set it manually.
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        if self.featured_image and hasattr(self.featured_image, 'file'):
            try:
                if self.featured_image.size > 1 * 1024 * 1024:
                    self.featured_image = resize_image(
                        self.featured_image, max_width=1200, max_height=800, quality=80
                    )
            except Exception:
                pass

        super().save(*args, **kwargs)

    @property
    def is_visible(self):
        """Whether this post should currently be shown to the public."""
        if self.status != 'published':
            return False
        if self.published_at and self.published_at > timezone.now():
            return False
        return True

    @property
    def reading_time(self):
        """Rough reading-time estimate (~200 words/minute), works fine for
        mixed Bengali/English content since it's just whitespace word count."""
        plain_text = re.sub(r'<[^>]+>', ' ', self.content or '')
        word_count = len(plain_text.split())
        return max(1, round(word_count / 200))

    def display_title(self, language='bn'):
        if language == 'en' and self.title_en:
            return self.title_en
        return self.title

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.excerpt

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'ব্লগ পোস্ট'
        verbose_name_plural = 'ব্লগ পোস্টসমূহ'
