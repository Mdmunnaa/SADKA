from django.db import models
from django.contrib.auth.models import User


class DonorProfile(models.Model):
    """Extra info linked to Django's built-in User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def total_donated(self):
        from donations.models import Donation
        from django.db.models import Sum
        total = Donation.objects.filter(
            donor_email=self.user.email,
            is_verified=True
        ).aggregate(t=Sum('amount'))['t']
        return total or 0

    @property
    def donation_count(self):
        from donations.models import Donation
        return Donation.objects.filter(
            donor_email=self.user.email,
            is_verified=True
        ).count()

    def __str__(self):
        return f"{self.display_name} ({self.user.email})"

    class Meta:
        verbose_name = 'ডোনার প্রোফাইল'
        verbose_name_plural = 'ডোনার প্রোফাইলসমূহ'
