from django.urls import path

from . import views

app_name = "visuals"

urlpatterns = [
    path("", views.component_gallery, name="component_gallery"),
]
