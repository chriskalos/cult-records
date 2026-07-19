from django.urls import path

from . import views


app_name = "cart"

urlpatterns = [
    path("", views.detail, name="detail"),
    path("add/<str:product_id>/", views.add, name="add"),
    path("update/<str:product_id>/", views.update, name="update"),
    path("remove/<str:product_id>/", views.remove, name="remove"),
]
