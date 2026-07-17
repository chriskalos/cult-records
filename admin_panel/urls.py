from django.urls import path

from . import views


app_name = "admin_panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users, name="users"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path(
        "users/<int:user_id>/password/",
        views.user_password,
        name="user_password",
    ),
    path("users/<int:user_id>/delete/", views.user_delete, name="user_delete"),
    path("products/", views.products, name="products"),
    path("products/add/", views.product_create, name="product_create"),
    path(
        "products/<str:product_id>/edit/",
        views.product_edit,
        name="product_edit",
    ),
    path(
        "products/<str:product_id>/visibility/",
        views.product_visibility,
        name="product_visibility",
    ),
    path(
        "products/<str:product_id>/delete/",
        views.product_delete,
        name="product_delete",
    ),
    path("bundles/", views.bundles, name="bundles"),
    path("reviews/", views.reviews, name="reviews"),
    path("activity/", views.activity, name="activity"),
    path("visuals/", views.visuals, name="visuals"),
]
