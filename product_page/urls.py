from django.urls import path

from . import views

app_name = "product_page"

urlpatterns = [
    path("products/<str:product_id>/", views.product_detail, name="detail"),
]
