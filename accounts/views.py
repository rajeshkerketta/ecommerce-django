from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login

from .models import SellerApplication, Profile, Seller
from .forms import SellerApplicationForm
from products.models import Order


# 🔐 LOGIN PAGE
def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔥 seller redirect FIXED
            if Seller.objects.filter(user=user, is_approved=True).exists():
                return redirect('seller_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# 👤 PROFILE PAGE
@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    latest_application = SellerApplication.objects.filter(
        user=request.user
    ).order_by('-created_at').first()

    orders_count = Order.objects.filter(user=request.user).count()

    if request.method == "POST":

        # 🗑 DELETE IMAGE
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
        "orders_count": orders_count,
        "latest_application": latest_application
    })


# 📦 ORDERS PAGE
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-id")

    return render(request, "my_orders.html", {
        "orders": orders
    })


# 🛍 BECOME SELLER
@login_required
def become_seller(request):

    # 🔥 FIX: seller check via Seller model
    if Seller.objects.filter(user=request.user, is_approved=True).exists():
        messages.info(request, "You are already an approved seller.")
        return redirect('profile')

    latest_application = SellerApplication.objects.filter(
        user=request.user
    ).order_by('-created_at').first()

    if latest_application and latest_application.status == 'pending':
        messages.warning(request, "Your seller application is already pending.")
        return redirect('profile')

    if latest_application and latest_application.status == 'approved':
        messages.info(request, "You are already approved as a seller.")
        return redirect('profile')

    if request.method == 'POST':
        form = SellerApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.status = 'pending'
            application.save()

            messages.success(request, "Application submitted. Wait for approval.")
            return redirect('profile')
    else:
        form = SellerApplicationForm()

    return render(request, 'accounts/become_seller.html', {'form': form})


# 🔁 RE-APPLY SELLER
@login_required
def reapply_seller(request):

    if Seller.objects.filter(user=request.user, is_approved=True).exists():
        messages.info(request, "You are already an approved seller.")
        return redirect('profile')

    latest_application = SellerApplication.objects.filter(
        user=request.user
    ).order_by('-created_at').first()

    if not latest_application:
        return redirect('become_seller')

    if latest_application.status == 'pending':
        messages.warning(request, "Application still pending.")
        return redirect('profile')

    if latest_application.status == 'approved':
        return redirect('profile')

    if request.method == 'POST':
        form = SellerApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.status = 'pending'
            application.save()

            messages.success(request, "Re-applied successfully.")
            return redirect('profile')
    else:
        form = SellerApplicationForm(initial={
            'shop_name': latest_application.shop_name,
            'phone': latest_application.phone,
            'address': latest_application.address,
            'business_type': latest_application.business_type,
            'gst_number': latest_application.gst_number,
            'description': latest_application.description,
        })

    return render(request, 'accounts/reapply_seller.html', {'form': form})