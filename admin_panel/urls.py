from django.urls import path

from . import views


app_name = "admin_panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users, name="users"),
    path("products/", views.products, name="products"),
    path("bundles/", views.bundles, name="bundles"),
    path("reviews/", views.reviews, name="reviews"),
    path("activity/", views.activity, name="activity"),
    path("visuals/", views.visuals, name="visuals"),
]
