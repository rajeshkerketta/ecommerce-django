from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile
from products.models import Order


def login_page(request):
    from django.http import HttpResponse
    return HttpResponse("Login Page")


# 👤 PROFILE PAGE
@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    orders_count = Order.objects.filter(user=request.user).count()

    if request.method == "POST":

        # 🗑 DELETE PROFILE IMAGE
        if request.POST.get("delete_image"):
            if profile.image:
                profile.image.delete(save=False)
                profile.image = None
                profile.save()
            return redirect("profile")

        # 📸 UPDATE IMAGE
        if request.FILES.get("image"):
            profile.image = request.FILES["image"]

        # 🧾 UPDATE DETAILS
        profile.phone = request.POST.get("phone", "")
        profile.address = request.POST.get("address", "")
        profile.landmark = request.POST.get("landmark", "")
        profile.city = request.POST.get("city", "")
        profile.state = request.POST.get("state", "")
        profile.pincode = request.POST.get("pincode", "")

        profile.save()
        return redirect("profile")

    return render(request, "accounts/profile.html", {
        "profile": profile,
        "orders_count": orders_count
    })


# 📦 ORDERS PAGE
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-id")

    return render(request, "my_orders.html", {
        "orders": orders
    })