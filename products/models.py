from django.db import models
from django.contrib.auth.models import User
from accounts.models import Seller


# ================= CATEGORY =================
class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategories'
    )

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


# ================= PRODUCT =================
class Product(models.Model):
    name = models.CharField(max_length=200)

    price = models.IntegerField()  # Selling price
    original_price = models.IntegerField(null=True, blank=True)  # MRP

    description = models.TextField()
    image = models.ImageField(upload_to='products/')

    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, blank=True, null=True)

    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    def average_rating(self):
        ratings = self.rating_set.all()
        if ratings.exists():
            return round(sum(r.value for r in ratings) / ratings.count(), 1)
        return 0

    def is_out_of_stock(self):
        return self.stock <= 0

    def stock_status(self):
        if not self.is_active:
            return "Inactive"
        if self.stock <= 0:
            return "Out of Stock"
        return "In Stock"

    def __str__(self):
        return self.name


# ================= PRODUCT IMAGES =================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")

    def __str__(self):
        return self.product.name


# ================= BANNER =================
class Banner(models.Model):
    image = models.ImageField(upload_to='banners/')
    title = models.CharField(max_length=100, blank=True)
    subtitle = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.title or "Banner"


# ================= ORDER =================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, default="0000000000")
    email = models.EmailField()

    address = models.TextField()
    landmark = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)

    payment_method = models.CharField(max_length=50, default="cod")

    total = models.IntegerField()

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    tracking_id = models.CharField(max_length=100, blank=True, null=True)

    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=500, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ================= ORDER ITEM =================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.IntegerField()

    def __str__(self):
        return self.product.name


# ================= RATING SYSTEM ⭐ =================
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    value = models.IntegerField()  # 1 to 5

    def __str__(self):
        return f"{self.product.name} - {self.value}"


# ================= WISHLIST ❤️ =================
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# ================= COUPON =================
class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount = models.IntegerField()  # % discount
    min_amount = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code