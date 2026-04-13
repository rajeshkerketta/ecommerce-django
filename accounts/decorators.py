from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Seller


def seller_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect("login")

        if request.user.is_staff:
            messages.info(request, "Admin can use admin panel.")
            return redirect("/admin/")

        seller = Seller.objects.filter(
            user=request.user,
            is_approved=True
        ).first()

        if not seller:
            messages.error(request, "You are not an approved seller.")
            return redirect("profile")

        return view_func(request, *args, **kwargs)

    return wrapper