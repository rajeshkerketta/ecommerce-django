
# Register your models here.
from django.contrib import admin
from .models import Seller


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ["id", "shop_name", "user", "phone", "is_approved"]
    search_fields = ["shop_name", "user__username", "phone"]
    list_filter = ["is_approved"]