from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category,
    Product,
    Order,
    OrderItem,
    ProductImage,
    Banner,
    Rating,
    Wishlist,
    Coupon,
)


# =========================
# HELPERS
# =========================
def get_discount_percentage(product):
    try:
        if getattr(product, "original_price", None) and product.original_price > product.price:
            discount = ((product.original_price - product.price) / product.original_price) * 100
            return f"{discount:.0f}% OFF"
    except Exception:
        pass
    return "-"


# =========================
# ORDER ITEM INLINE
# =========================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = [
        "product_image_preview",
        "product_name",
        "product_category",
        "product_stock",
        "product_price",
        "product_original_price",
        "product_discount",
        "product_short_description",
        "line_total",
    ]
    fields = [
        "product",
        "product_name",
        "product_category",
        "product_stock",
        "product_image_preview",
        "quantity",
        "product_price",
        "product_original_price",
        "product_discount",
        "line_total",
        "product_short_description",
    ]

    def product_image_preview(self, obj):
        if obj.product and getattr(obj.product, "image", None):
            return format_html(
                '<img src="{}" width="70" height="70" '
                'style="object-fit:cover;border-radius:8px;border:1px solid #ddd;" />',
                obj.product.image.url,
            )
        return "No Image"

    product_image_preview.short_description = "Product Image"

    def product_name(self, obj):
        if obj.product:
            return obj.product.name
        return "-"

    product_name.short_description = "Product Name"

    def product_category(self, obj):
        if obj.product and getattr(obj.product, "category", None):
            return obj.product.category.name
        return "-"

    product_category.short_description = "Category"

    def product_stock(self, obj):
        if obj.product:
            return getattr(obj.product, "stock", "-")
        return "-"

    product_stock.short_description = "Stock"

    def product_price(self, obj):
        if obj.product:
            return f"₹{obj.product.price}"
        return "-"

    product_price.short_description = "Unit Price"

    def product_original_price(self, obj):
        if obj.product:
            original_price = getattr(obj.product, "original_price", None)
            if original_price:
                return f"₹{original_price}"
        return "-"

    product_original_price.short_description = "Original Price"

    def product_discount(self, obj):
        if obj.product:
            return get_discount_percentage(obj.product)
        return "-"

    product_discount.short_description = "Discount"

    def product_short_description(self, obj):
        if obj.product:
            desc = getattr(obj.product, "description", "")
            if desc:
                return desc[:80] + "..." if len(desc) > 80 else desc
        return "-"

    product_short_description.short_description = "Short Description"

    def line_total(self, obj):
        if obj.product:
            return f"₹{obj.product.price * obj.quantity}"
        return "-"

    line_total.short_description = "Line Total"


# =========================
# PRODUCT IMAGE INLINE
# =========================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    readonly_fields = ["image_preview"]
    fields = ["image", "image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="80" '
                'style="object-fit:cover;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return "No Image"

    image_preview.short_description = "Preview"


# =========================
# CATEGORY ADMIN
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "parent"]
    search_fields = ["name", "parent__name"]
    list_filter = ["parent"]


# =========================
# PRODUCT ADMIN
# =========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]

    list_display = [
        "id",
        "image_preview_small",
        "name",
        "seller",
        "category",
        "stock",
        "stock_status_display",
        "is_active",
        "price",
        "original_price_display",
        "discount_display",
    ]
    search_fields = ["name", "description", "seller__shop_name", "category__name"]
    list_filter = ["category", "seller", "is_active"]
    list_editable = ["stock", "is_active"]
    readonly_fields = [
        "image_preview_large",
        "discount_display",
        "short_description_display",
        "stock_status_display",
    ]

    fields = [
        "image_preview_large",
        "seller",
        "name",
        "category",
        "stock",
        "is_active",
        "stock_status_display",
        "description",
        "short_description_display",
        "price",
        "original_price",
        "discount_display",
        "image",
    ]

    def image_preview_small(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="55" height="55" '
                'style="object-fit:cover;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return "No Image"

    image_preview_small.short_description = "Preview"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="180" '
                'style="border-radius:12px;border:1px solid #ddd;box-shadow:0 4px 12px rgba(0,0,0,0.08);" />',
                obj.image.url,
            )
        return "No Image"

    image_preview_large.short_description = "Current Image"

    def original_price_display(self, obj):
        if getattr(obj, "original_price", None):
            return f"₹{obj.original_price}"
        return "-"

    original_price_display.short_description = "Original Price"

    def discount_display(self, obj):
        return get_discount_percentage(obj)

    discount_display.short_description = "Discount"

    def short_description_display(self, obj):
        desc = getattr(obj, "description", "")
        if desc:
            return desc[:120] + "..." if len(desc) > 120 else desc
        return "-"

    short_description_display.short_description = "Short Description"

    def stock_status_display(self, obj):
        if not obj.is_active:
            return "Inactive"
        if obj.stock <= 0:
            return "Out of Stock"
        return "In Stock"

    stock_status_display.short_description = "Stock Status"


# =========================
# ORDER ADMIN
# =========================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "name",
        "phone",
        "email",
        "total",
        "status",
        "tracking_id",
        "payment_method_display",
        "created_at",
        "is_paid",
    ]
    list_filter = ["status", "created_at", "is_paid"]
    search_fields = ["name", "email", "phone", "tracking_id", "user__username"]
    inlines = [OrderItemInline]

    readonly_fields = [
        "user",
        "name",
        "email",
        "phone",
        "address",
        "landmark",
        "city",
        "state",
        "pincode",
        "total",
        "payment_method_display",
        "tracking_id",
        "created_at",
        "is_paid",
    ]

    fields = [
        "user",
        "name",
        "email",
        "phone",
        "address",
        "landmark",
        "city",
        "state",
        "pincode",
        "total",
        "payment_method_display",
        "status",
        "tracking_id",
        "is_paid",
        "created_at",
    ]

    def payment_method_display(self, obj):
        if obj.payment_method == "cod":
            return "Cash on Delivery"
        elif obj.payment_method == "razorpay":
            return "Online Payment"
        return obj.payment_method

    payment_method_display.short_description = "Payment Method"


# =========================
# ORDER ITEM ADMIN
# =========================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "product",
        "product_image_preview",
        "quantity",
        "product_price",
        "line_total",
    ]
    search_fields = ["order__id", "product__name"]
    readonly_fields = [
        "product_image_preview",
        "product_name",
        "product_category",
        "product_stock",
        "product_price",
        "product_original_price",
        "product_discount",
        "product_short_description",
        "line_total",
    ]

    fields = [
        "order",
        "product",
        "product_name",
        "product_category",
        "product_stock",
        "product_image_preview",
        "quantity",
        "product_price",
        "product_original_price",
        "product_discount",
        "line_total",
        "product_short_description",
    ]

    def product_image_preview(self, obj):
        if obj.product and getattr(obj.product, "image", None):
            return format_html(
                '<img src="{}" width="60" height="60" '
                'style="object-fit:cover;border-radius:8px;border:1px solid #ddd;" />',
                obj.product.image.url,
            )
        return "No Image"

    product_image_preview.short_description = "Preview"

    def product_name(self, obj):
        if obj.product:
            return obj.product.name
        return "-"

    product_name.short_description = "Product Name"

    def product_category(self, obj):
        if obj.product and getattr(obj.product, "category", None):
            return obj.product.category.name
        return "-"

    product_category.short_description = "Category"

    def product_stock(self, obj):
        if obj.product:
            return getattr(obj.product, "stock", "-")
        return "-"

    product_stock.short_description = "Stock"

    def product_price(self, obj):
        if obj.product:
            return f"₹{obj.product.price}"
        return "-"

    product_price.short_description = "Unit Price"

    def product_original_price(self, obj):
        if obj.product:
            original_price = getattr(obj.product, "original_price", None)
            if original_price:
                return f"₹{original_price}"
        return "-"

    product_original_price.short_description = "Original Price"

    def product_discount(self, obj):
        if obj.product:
            return get_discount_percentage(obj.product)
        return "-"

    product_discount.short_description = "Discount"

    def product_short_description(self, obj):
        if obj.product:
            desc = getattr(obj.product, "description", "")
            if desc:
                return desc[:80] + "..." if len(desc) > 80 else desc
        return "-"

    product_short_description.short_description = "Short Description"

    def line_total(self, obj):
        if obj.product:
            return f"₹{obj.product.price * obj.quantity}"
        return "-"

    line_total.short_description = "Line Total"


# =========================
# PRODUCT IMAGE ADMIN
# =========================
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "image_preview"]
    search_fields = ["product__name"]
    readonly_fields = ["image_preview"]
    fields = ["product", "image", "image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="120" '
                'style="border-radius:10px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return "No Image"

    image_preview.short_description = "Preview"


# =========================
# BANNER ADMIN
# =========================
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["id", "banner_preview"]
    readonly_fields = ["banner_preview"]

    def banner_preview(self, obj):
        if hasattr(obj, "image") and obj.image:
            return format_html(
                '<img src="{}" width="180" '
                'style="border-radius:10px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return "No Image"

    banner_preview.short_description = "Banner Preview"


# =========================
# RATING ADMIN
# =========================
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "value"]
    search_fields = ["user__username", "product__name"]
    list_filter = ["value"]


# =========================
# WISHLIST ADMIN
# =========================
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product"]
    search_fields = ["user__username", "product__name"]


# =========================
# COUPON ADMIN
# =========================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "discount"]
    search_fields = ["code"]