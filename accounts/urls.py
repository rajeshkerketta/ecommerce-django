from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("my-orders/", views.my_orders, name="my_orders"),
]