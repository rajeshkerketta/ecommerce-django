from django.contrib import admin
from .models import Seller, Profile, SellerApplication


# =========================
# SELLER ADMIN
# =========================
@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ["id", "shop_name", "user", "phone", "is_approved"]
    search_fields = ["shop_name", "user__username", "phone"]
    list_filter = ["is_approved"]


# =========================
# PROFILE ADMIN
# =========================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'pincode', 'is_seller']
    search_fields = ['user__username', 'city', 'pincode']


# =========================
# SELLER APPLICATION ADMIN
# =========================
@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'shop_name', 'phone', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'shop_name', 'phone']

    actions = ['approve_sellers']

    def approve_sellers(self, request, queryset):
        for app in queryset:

            # ✅ Seller create/update
            seller, created = Seller.objects.get_or_create(user=app.user)
            seller.shop_name = app.shop_name
            seller.phone = app.phone
            seller.address = app.address
            seller.is_approved = True
            seller.save()

            # ✅ Application approve
            app.status = 'approved'
            app.save()

            # 🔥 IMPORTANT FIX
            profile, created = Profile.objects.get_or_create(user=app.user)
            profile.is_seller = True
            profile.save()

        self.message_user(request, "Selected sellers approved successfully")

    approve_sellers.short_description = "Approve selected seller applications"