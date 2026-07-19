from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.AccountLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "orders/<uuid:order_id>/delivered/",
        views.mark_order_delivered,
        name="mark_order_delivered",
    ),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
]
