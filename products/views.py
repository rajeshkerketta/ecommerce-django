from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from accounts.decorators import seller_required
from django.contrib.auth.models import User

import razorpay

from accounts.decorators import seller_required
from accounts.models import Seller

from .models import (
    Product,
    Category,
    Order,
    OrderItem,
    Banner,
    Wishlist,
    Rating,
    Coupon,
    ProductImage,
)
from .forms import SellerProductForm


# ================= COMMON =================
def get_cart_count(request):
    cart = request.session.get('cart', {})
    return sum(cart.values())


def validate_cart_stock(request):
    """
    Returns (is_valid, products, total)
    """
    cart = request.session.get('cart', {})
    products = []
    total = 0

    for id, qty in cart.items():
        product = get_object_or_404(Product, id=id)

        if product.stock <= 0:
            messages.error(request, f"{product.name} is out of stock.")
            return False, [], 0

        if qty > product.stock:
            cart[str(id)] = product.stock
            request.session['cart'] = cart
            messages.warning(
                request,
                f"Quantity for {product.name} was adjusted to available stock ({product.stock})."
            )
            qty = product.stock

        product.qty = qty
        product.subtotal = product.price * qty
        total += product.subtotal
        products.append(product)

    return True, products, total


def reduce_stock_after_order(products):
    for product in products:
        product.stock -= product.qty
        if product.stock < 0:
            product.stock = 0
        product.save()


# ================= HOME =================
def home(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    products = products.order_by('-id')

    wishlist_products = []
    if request.user.is_authenticated:
        wishlist_products = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )

    for product in products:
        rating_data = Rating.objects.filter(product=product).aggregate(
            avg=Avg('value'),
            count=Count('id')
        )
        product.avg_rating = rating_data['avg'] or 0
        product.review_count = rating_data['count'] or 0

    return render(request, 'home.html', {
        'products': products,
        'categories': Category.objects.all(),
        'banners': Banner.objects.all(),
        'query': query,
        'cart_count': get_cart_count(request),
        'wishlist_products': wishlist_products,
    })


# ================= SHOP =================
def shop(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    search = request.GET.get('q')
    category = request.GET.get('category')
    sort = request.GET.get('sort')
    min_price = request.GET.get('min')
    max_price = request.GET.get('max')

    wishlist_products = []

    if request.user.is_authenticated:
        wishlist_products = list(
            Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        )

    if search:
        products = products.filter(name__icontains=search)

    if category:
        products = products.filter(category_id=category)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if sort == "low":
        products = products.order_by('price')
    elif sort == "high":
        products = products.order_by('-price')
    else:
        products = products.order_by('-id')

    for product in products:
        rating_data = Rating.objects.filter(product=product).aggregate(
            avg=Avg('value'),
            count=Count('id')
        )
        product.average_rating = rating_data['avg'] or 0
        product.review_count = rating_data['count'] or 0

    return render(request, "shop.html", {
        "products": products,
        "categories": categories,
        "cart_count": get_cart_count(request),
        "wishlist_products": wishlist_products
    })


# ================= PRODUCT DETAIL =================
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    images = product.images.all()

    return render(request, "product_detail.html", {
        "product": product,
        "images": images
    })


# ================= CART =================
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect('product_detail', id=id)

    cart = request.session.get('cart', {})
    current_qty = cart.get(str(id), 0)

    if current_qty >= product.stock:
        messages.warning(request, f"Only {product.stock} item(s) available for {product.name}.")
        return redirect('cart')

    cart[str(id)] = current_qty + 1
    request.session['cart'] = cart
    messages.success(request, f"{product.name} added to cart.")
    return redirect('cart')


def add_to_cart_ajax(request, id):
    product = get_object_or_404(Product, id=id)

    if product.stock <= 0:
        return JsonResponse({
            'count': get_cart_count(request),
            'error': 'out_of_stock',
            'message': f'{product.name} is out of stock.'
        })

    cart = request.session.get('cart', {})
    current_qty = cart.get(str(id), 0)

    if current_qty >= product.stock:
        return JsonResponse({
            'count': sum(cart.values()),
            'error': 'stock_limit',
            'message': f'Only {product.stock} item(s) available.'
        })

    cart[str(id)] = current_qty + 1
    request.session['cart'] = cart

    return JsonResponse({
        'count': sum(cart.values()),
        'message': 'Added to cart'
    })


def buy_now(request, id):
    product = get_object_or_404(Product, id=id)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect('product_detail', id=id)

    cart = request.session.get('cart', {})
    cart[str(id)] = 1
    request.session['cart'] = cart
    return redirect('checkout')


def cart(request):
    is_valid, products, total = validate_cart_stock(request)

    if not is_valid:
        return redirect('shop')

    request.session['total'] = total

    return render(request, "cart.html", {
        "products": products,
        "total": total
    })


def increase_qty(request, id):
    product = get_object_or_404(Product, id=id)
    cart = request.session.get('cart', {})

    if str(id) not in cart:
        return redirect('cart')

    if cart[str(id)] >= product.stock:
        messages.warning(request, f"Only {product.stock} item(s) available for {product.name}.")
        return redirect('cart')

    cart[str(id)] += 1
    request.session['cart'] = cart
    return redirect('cart')


def decrease_qty(request, id):
    cart = request.session.get('cart', {})

    if str(id) in cart:
        cart[str(id)] -= 1
        if cart[str(id)] <= 0:
            del cart[str(id)]

    request.session['cart'] = cart
    return redirect('cart')


def remove_cart(request, id):
    cart = request.session.get('cart', {})
    cart.pop(str(id), None)
    request.session['cart'] = cart
    return redirect('cart')


# ================= SIGNUP =================
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('shop')
    else:
        form = UserCreationForm()

    return render(request, "signup.html", {"form": form})


# ================= CHECKOUT =================
@login_required
def checkout(request):
    from accounts.models import Profile

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    is_valid, products, total = validate_cart_stock(request)
    if not is_valid:
        return redirect("cart")

    profile, created = Profile.objects.get_or_create(user=request.user)

    coupon = request.session.get('coupon')
    discount = coupon['discount'] if coupon else 0
    final_total = total - discount

    if final_total < 1:
        final_total = 1

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        for product in products:
            if product.qty > product.stock:
                messages.error(request, f"Not enough stock for {product.name}.")
                return redirect("cart")

        if payment_method == "cod":
            order = Order.objects.create(
                user=request.user,
                name=request.POST.get("name"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                address=request.POST.get("address"),
                landmark=request.POST.get("landmark"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
                payment_method="cod",
                total=final_total,
                status="pending"
            )

            for product in products:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=product.qty
                )

            reduce_stock_after_order(products)

            request.session['cart'] = {}
            request.session['coupon'] = {}
            return redirect('order_success')

    razorpay_order_id = None

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        payment_data = {
            "amount": int(final_total * 100),
            "currency": "INR",
            "payment_capture": 1
        }

        razorpay_order = client.order.create(data=payment_data)
        razorpay_order_id = razorpay_order.get("id")

    except Exception as e:
        print("Razorpay order creation failed:", e)
        messages.warning(request, "Online payment is temporarily unavailable. You can still place Cash on Delivery.")

    return render(request, "checkout.html", {
        "products": products,
        "total": total,
        "final_total": final_total,
        "profile": profile,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": razorpay_order_id,
    })


# ================= ORDERS =================
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, "my_orders.html", {
        "orders": orders
    })


@login_required
def order_success(request):
    latest_order = Order.objects.filter(user=request.user).order_by('-created_at').first()

    return render(request, "order_success.html", {
        "latest_order": latest_order
    })


# ================= WISHLIST =================
@login_required
def toggle_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)

    item = Wishlist.objects.filter(user=request.user, product=product)

    if item.exists():
        item.delete()
        return JsonResponse({'status': 'removed'})
    else:
        Wishlist.objects.create(user=request.user, product=product)
        return JsonResponse({'status': 'added'})


@login_required
def wishlist_page(request):
    items = Wishlist.objects.filter(user=request.user)

    return render(request, "wishlist.html", {
        "items": items
    })


# ================= RATING =================
@login_required
def add_rating(request, product_id, value):
    product = Product.objects.get(id=product_id)

    rating, created = Rating.objects.get_or_create(
        user=request.user,
        product=product
    )

    rating.value = value
    rating.save()

    return JsonResponse({'status': 'ok'})


# ================= ORDER DETAIL =================
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)

    return render(request, "order_detail.html", {
        "order": order,
        "items": items
    })


# ================= CANCEL ORDER =================
@login_required
def cancel_order(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)

    if order.status in ['pending', 'confirmed']:
        order.status = 'cancelled'
        order.save()

        items = OrderItem.objects.filter(order=order)
        for item in items:
            item.product.stock += item.quantity
            item.product.save()

    return redirect('my_orders')


# ================= COUPON =================
def apply_coupon(request):
    code = request.POST.get('code')

    try:
        coupon = Coupon.objects.get(code__iexact=code, active=True)

        cart_total = request.session.get('total', 0)

        if cart_total < coupon.min_amount:
            messages.error(request, "Minimum order not met")
            return redirect('checkout')

        discount = (cart_total * coupon.discount) // 100

        request.session['coupon'] = {
            'code': coupon.code,
            'discount': discount
        }

        messages.success(request, "Coupon applied successfully")

    except Coupon.DoesNotExist:
        messages.error(request, "Invalid coupon")

    return redirect('checkout')


# ================= PAYMENT SUCCESS =================
@csrf_exempt
@login_required
def payment_success(request):
    if request.method == "POST":
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")
        landmark = request.POST.get("landmark")
        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            messages.error(request, "Payment details missing.")
            return redirect("checkout")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })

            cart = request.session.get('cart', {})
            if not cart:
                messages.error(request, "Your cart is empty.")
                return redirect("cart")

            is_valid, products, total = validate_cart_stock(request)
            if not is_valid:
                return redirect("cart")

            coupon = request.session.get('coupon')
            discount = coupon['discount'] if coupon else 0

            final_total = total - discount
            if final_total < 1:
                final_total = 1

            for product in products:
                if product.qty > product.stock:
                    messages.error(request, f"Not enough stock for {product.name}.")
                    return redirect("cart")

            order = Order.objects.create(
                user=request.user,
                name=name,
                email=email,
                phone=phone,
                address=address,
                landmark=landmark,
                city=city,
                state=state,
                pincode=pincode,
                payment_method="razorpay",
                total=final_total,
                status="confirmed",
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                is_paid=True
            )

            for product in products:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=product.qty
                )

            reduce_stock_after_order(products)

            request.session['cart'] = {}
            request.session['coupon'] = {}

            return redirect("order_success")

        except Exception as e:
            print("Payment verification failed:", e)
            messages.error(request, "Payment verification failed.")
            return redirect("checkout")

    return redirect("checkout")


# ================= SELLER DASHBOARD =================
@seller_required
def seller_dashboard(request):
    seller = Seller.objects.get(user=request.user, is_approved=True)

    seller_products = Product.objects.filter(seller=seller)
    seller_order_items = OrderItem.objects.filter(product__seller=seller).select_related("order", "product")

    total_products = seller_products.count()
    total_orders = seller_order_items.values("order").distinct().count()
    pending_orders = seller_order_items.filter(order__status="pending").values("order").distinct().count()
    delivered_orders = seller_order_items.filter(order__status="delivered").values("order").distinct().count()
    cancelled_orders = seller_order_items.filter(order__status="cancelled").values("order").distinct().count()

    total_sales = sum(
        item.product.price * item.quantity
        for item in seller_order_items.filter(order__status="delivered")
    )

    pending_revenue = sum(
        item.product.price * item.quantity
        for item in seller_order_items.filter(
            order__status__in=["pending", "confirmed", "packed", "shipped", "out_for_delivery"]
        )
    )

    delivered_revenue = total_sales

    low_stock_products = seller_products.filter(stock__gt=0, stock__lte=5).count()
    out_of_stock_products = seller_products.filter(stock__lte=0).count()

    recent_products = seller_products.order_by("-id")[:6]
    recent_order_items = seller_order_items.order_by("-order__created_at")[:8]

    # Category analytics
    category_data = []
    category_map = {}
    for product in seller_products.select_related("category"):
        category_name = product.category.name if product.category else "No Category"
        category_map[category_name] = category_map.get(category_name, 0) + 1
    for name, count in category_map.items():
        category_data.append({"name": name, "count": count})

    category_labels = list(category_map.keys())
    category_counts = list(category_map.values())

    # Order status chart
    status_labels = ["Pending", "Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered", "Cancelled"]
    status_counts = [
        seller_order_items.filter(order__status="pending").count(),
        seller_order_items.filter(order__status="confirmed").count(),
        seller_order_items.filter(order__status="packed").count(),
        seller_order_items.filter(order__status="shipped").count(),
        seller_order_items.filter(order__status="out_for_delivery").count(),
        seller_order_items.filter(order__status="delivered").count(),
        seller_order_items.filter(order__status="cancelled").count(),
    ]

    # Top selling products
    product_sales = {}
    for item in seller_order_items.filter(order__status="delivered"):
        product_id = item.product.id
        if product_id not in product_sales:
            product_sales[product_id] = {
                "name": item.product.name,
                "qty": 0,
                "revenue": 0,
            }
        product_sales[product_id]["qty"] += item.quantity
        product_sales[product_id]["revenue"] += item.product.price * item.quantity

    top_products_sorted = sorted(
        product_sales.values(),
        key=lambda x: x["qty"],
        reverse=True
    )[:5]

    top_product_labels = [item["name"] for item in top_products_sorted]
    top_product_qty = [item["qty"] for item in top_products_sorted]

    # Monthly sales
    month_map = {}
    delivered_items = seller_order_items.filter(order__status="delivered").order_by("order__created_at")

    for item in delivered_items:
        month_key = item.order.created_at.strftime("%b %Y")
        month_map[month_key] = month_map.get(month_key, 0) + (item.product.price * item.quantity)

    monthly_labels = list(month_map.keys())[-6:]
    monthly_sales = list(month_map.values())[-6:]

    # Customer analytics
    customer_map = {}
    city_map = {}
    state_map = {}

    for item in seller_order_items:
        order = item.order
        customer_key = order.email or order.phone or order.name

        if customer_key not in customer_map:
            customer_map[customer_key] = {
                "name": order.name or "Customer",
                "email": order.email or "-",
                "phone": order.phone or "-",
                "orders": set(),
                "items": 0,
                "spent": 0,
                "city": order.city or "-",
                "state": order.state or "-",
            }

        customer_map[customer_key]["orders"].add(order.id)
        customer_map[customer_key]["items"] += item.quantity

        if order.status == "delivered":
            customer_map[customer_key]["spent"] += item.product.price * item.quantity

        if order.city:
            city_map[order.city] = city_map.get(order.city, 0) + 1
        if order.state:
            state_map[order.state] = state_map.get(order.state, 0) + 1

    unique_customers = len(customer_map)

    top_buyers = []
    for _, data in customer_map.items():
        data["order_count"] = len(data["orders"])
        top_buyers.append(data)

    top_buyers = sorted(
        top_buyers,
        key=lambda x: (x["spent"], x["items"], x["order_count"]),
        reverse=True
    )[:5]

    recent_customers = sorted(
        top_buyers,
        key=lambda x: (x["order_count"], x["items"]),
        reverse=True
    )[:5]

    city_stats = sorted(city_map.items(), key=lambda x: x[1], reverse=True)[:5]
    state_stats = sorted(state_map.items(), key=lambda x: x[1], reverse=True)[:5]

    context = {
        "seller": seller,
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "total_sales": total_sales,
        "pending_revenue": pending_revenue,
        "delivered_revenue": delivered_revenue,
        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock_products,
        "recent_products": recent_products,
        "recent_order_items": recent_order_items,
        "status_labels": status_labels,
        "status_counts": status_counts,
        "top_product_labels": top_product_labels,
        "top_product_qty": top_product_qty,
        "top_products_data": top_products_sorted,
        "monthly_labels": monthly_labels,
        "monthly_sales": monthly_sales,
        "category_labels": category_labels,
        "category_counts": category_counts,
        "category_data": category_data,
        "unique_customers": unique_customers,
        "top_buyers": top_buyers,
        "recent_customers": recent_customers,
        "city_stats": city_stats,
        "state_stats": state_stats,
    }
    return render(request, "seller/dashboard.html", context)


# ================= SELLER PRODUCTS =================
@seller_required
def seller_products(request):
    seller = Seller.objects.get(user=request.user, is_approved=True)
    products = Product.objects.filter(seller=seller).order_by("-id")

    return render(request, "seller/products_list.html", {
        "seller": seller,
        "products": products,
    })


@seller_required
def seller_add_product(request):
    seller = Seller.objects.get(user=request.user, is_approved=True)

    if request.method == "POST":
        form = SellerProductForm(request.POST, request.FILES)
        files = request.FILES.getlist("extra_images")

        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller
            product.save()

            for image_file in files:
                ProductImage.objects.create(product=product, image=image_file)

            messages.success(request, "Product added successfully.")
            return redirect("seller_products")
        else:
            print("FORM ERRORS:", form.errors)
            messages.error(request, f"Form error: {form.errors}")
    else:
        form = SellerProductForm()

    return render(request, "seller/product_form.html", {
        "form": form,
        "page_title": "Add Product",
        "button_text": "Add Product",
    })


@seller_required
def seller_edit_product(request, product_id):
    seller = Seller.objects.get(user=request.user, is_approved=True)
    product = get_object_or_404(Product, id=product_id, seller=seller)

    if request.method == "POST":
        form = SellerProductForm(request.POST, request.FILES, instance=product)
        files = request.FILES.getlist("extra_images")

        if form.is_valid():
            updated_product = form.save(commit=False)
            updated_product.seller = seller
            updated_product.save()

            for image_file in files:
                ProductImage.objects.create(product=updated_product, image=image_file)

            messages.success(request, "Product updated successfully.")
            return redirect("seller_products")
        else:
            print("FORM ERRORS:", form.errors)
            messages.error(request, f"Form error: {form.errors}")
    else:
        form = SellerProductForm(instance=product)

    return render(request, "seller/product_form.html", {
        "form": form,
        "page_title": "Edit Product",
        "button_text": "Update Product",
        "product": product,
        "extra_images": product.images.all(),
    })


@seller_required
def seller_delete_product(request, product_id):
    seller = Seller.objects.get(user=request.user, is_approved=True)
    product = get_object_or_404(Product, id=product_id, seller=seller)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect("seller_products")

    return render(request, "seller/product_delete.html", {
        "product": product,
    })


# ================= SELLER ORDERS =================
@seller_required
def seller_orders(request):
    seller = Seller.objects.get(user=request.user, is_approved=True)

    order_items = OrderItem.objects.filter(
        product__seller=seller
    ).select_related("order", "product").order_by("-order__created_at")

    return render(request, "seller/orders.html", {
        "order_items": order_items
    })


# ================= SELLER ORDER DETAIL =================
@seller_required
def seller_order_detail(request, order_id):
    seller = Seller.objects.get(user=request.user, is_approved=True)

    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order, product__seller=seller)

    return render(request, "seller/order_detail.html", {
        "order": order,
        "items": items
    })


# ================= UPDATE ORDER STATUS =================
@seller_required
def update_order_status(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)

        status = request.POST.get("status")
        tracking_id = request.POST.get("tracking_id")

        order.status = status

        if tracking_id:
            order.tracking_id = tracking_id

        order.save()

    return redirect("seller_order_detail", order_id=order_id)


# ================= DELETE EXTRA IMAGE =================
@seller_required
def delete_extra_image(request, id):
    image = get_object_or_404(ProductImage, id=id)

    if image.product.seller.user != request.user:
        messages.error(request, "Unauthorized action.")
        return redirect("seller_dashboard")

    image.delete()
    messages.success(request, "Image deleted successfully.")

    return redirect(request.META.get('HTTP_REFERER', 'seller_products'))

#==========================================================================



def create_admin(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@gmail.com", "admin123")
    return HttpResponse("Admin created")