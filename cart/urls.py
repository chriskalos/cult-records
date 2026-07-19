from django.urls import path

from . import views


app_name = "cart"

urlpatterns = [
    path("", views.detail, name="detail"),
    path("add/<str:product_id>/", views.add, name="add"),
    path("update/<str:product_id>/", views.update, name="update"),
    path("remove/<str:product_id>/", views.remove, name="remove"),
    path("checkout/", views.checkout_start, name="checkout_start"),
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path(
        "checkout/cancel/<uuid:order_id>/",
        views.checkout_cancel,
        name="checkout_cancel",
    ),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]
