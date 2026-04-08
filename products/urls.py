from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),

    path('product/<int:id>/', views.product_detail, name='product_detail'),

    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('add-to-cart-ajax/<int:id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),

    path('buy-now/<int:id>/', views.buy_now, name='buy_now'),
    path('cart/', views.cart, name='cart'),
    path('increase/<int:id>/', views.increase_qty, name='increase_qty'),
    path('decrease/<int:id>/', views.decrease_qty, name='decrease_qty'),
    path('remove/<int:id>/', views.remove_cart, name='remove_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('signup/', views.signup, name='signup'),

    path('my-orders/', views.my_orders, name='my_orders'),
    path('orders/', views.my_orders, name='orders'),

    path('order-success/', views.order_success, name='order_success'),

    path('wishlist/', views.wishlist_page, name='wishlist_page'),
    path('wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    path('rate/<int:product_id>/<int:value>/', views.add_rating, name='add_rating'),

    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel-order/<int:id>/', views.cancel_order, name='cancel_order'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('payment-success/', views.payment_success, name='payment_success'),

    # SELLER DASHBOARD
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),

    # SELLER PRODUCT MANAGEMENT
    path('seller/products/', views.seller_products, name='seller_products'),
    path('seller/products/add/', views.seller_add_product, name='seller_add_product'),
    path('seller/products/<int:product_id>/edit/', views.seller_edit_product, name='seller_edit_product'),
    path('seller/products/<int:product_id>/delete/', views.seller_delete_product, name='seller_delete_product'),

    # SELLER ORDER MANAGEMENT
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/orders/<int:order_id>/', views.seller_order_detail, name='seller_order_detail'),
    path('seller/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    # DELETE EXTRA IMAGE
    path('seller/image/delete/<int:id>/', views.delete_extra_image, name='delete_extra_image'),
]