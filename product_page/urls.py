from django.urls import path

from . import views

app_name = "product_page"

urlpatterns = [
    path("products/<str:product_id>/", views.product_detail, name="detail"),
    path(
        "products/<str:product_id>/reviews/",
        views.create_review,
        name="review_create",
    ),
    path(
        "products/<str:product_id>/reviews/<int:review_id>/edit/",
        views.edit_review,
        name="review_edit",
    ),
    path(
        "products/<str:product_id>/reviews/<int:review_id>/delete/",
        views.delete_review,
        name="review_delete",
    ),
]
