from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='heart')  # Bootstrap icon name

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('active', 'চলমান'),
        ('completed', 'সম্পন্ন'),
        ('urgent', 'জরুরি'),
        ('paused', 'বিরতি'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='campaigns/', blank=True, null=True)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    raised_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bkash_number = models.CharField(max_length=20, blank=True, help_text="বিকাশ নম্বর")
    nagad_number = models.CharField(max_length=20, blank=True, help_text="নগদ নম্বর")
    rocket_number = models.CharField(max_length=20, blank=True, help_text="রকেট নম্বর")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Campaign.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def progress_percent(self):
        if self.target_amount > 0:
            percent = (self.raised_amount / self.target_amount) * 100
            return min(int(percent), 100)
        return 0

    @property
    def donor_count(self):
        return self.donations.filter(is_verified=True).count()

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.raised_amount, 0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-is_featured', '-created_at']


class CampaignUpdate(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='updates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campaign.title} - {self.title}"

    class Meta:
        ordering = ['-created_at']
