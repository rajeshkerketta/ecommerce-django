from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, SellerApplication


# =========================
# AUTO CREATE PROFILE
# =========================
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# =========================
# AUTO SAVE PROFILE
# =========================
@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# =========================
# SELLER STATUS SYNC
# =========================
@receiver(post_save, sender=SellerApplication)
def update_user_seller_status(sender, instance, **kwargs):
    profile, created = Profile.objects.get_or_create(user=instance.user)

    # ✅ APPROVED → seller ban jao
    if instance.status == 'approved':
        profile.is_seller = True
        profile.save()

    # ❌ REJECTED / PENDING → only if no approved exists
    else:
        approved_exists = SellerApplication.objects.filter(
            user=instance.user,
            status='approved'
        ).exists()

        if not approved_exists:
            profile.is_seller = False
            profile.save()