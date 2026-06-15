from django.db import models
from campaigns.models import Campaign
import uuid


class Donation(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('bkash', 'বিকাশ'),
        ('nagad', 'নগদ'),
        ('rocket', 'রকেট'),
        ('bank', 'ব্যাংক'),
        ('cash', 'নগদ অর্থ'),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='donations')
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    donor_name = models.CharField(max_length=200, blank=True, default='')
    donor_phone = models.CharField(max_length=20, blank=True)
    donor_email = models.EmailField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bkash')
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Transaction/Reference নম্বর")
    is_anonymous = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_verified = False
        if not is_new:
            old = Donation.objects.filter(pk=self.pk).first()
            if old:
                was_verified = old.is_verified

        super().save(*args, **kwargs)

        # Update campaign raised amount when verified
        if self.is_verified and not was_verified:
            campaign = self.campaign
            from django.db.models import Sum
            total = Donation.objects.filter(
                campaign=campaign, is_verified=True
            ).aggregate(total=Sum('amount'))['total'] or 0
            campaign.raised_amount = total
            campaign.save(update_fields=['raised_amount'])

    @property
    def display_name(self):
        if self.is_anonymous:
            return "একজন শুভাকাঙ্ক্ষী"
        return self.donor_name or "অজ্ঞাত দাতা"

    def __str__(self):
        return f"{self.display_name} - ৳{self.amount} ({self.campaign.title})"

    class Meta:
        ordering = ['-created_at']
