from .models import Seller


def is_seller(user):
    if not user.is_authenticated:
        return False
    return Seller.objects.filter(user=user, is_approved=True).exists()