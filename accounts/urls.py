from django.urls import path
from . import views

urlpatterns = [

    # 🔐 AUTH
    path("login/", views.login_page, name="login"),

    # 👤 PROFILE
    path("profile/", views.profile, name="profile"),

    # 📦 ORDERS
    path("my-orders/", views.my_orders, name="my_orders"),

    # 🛍 SELLER
    path("become-seller/", views.become_seller, name="become_seller"),
    path("reapply-seller/", views.reapply_seller, name="reapply_seller"),
]