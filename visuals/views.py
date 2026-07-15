from django.shortcuts import render

from home.models import Product


def component_gallery(request):
    product = Product.objects.order_by("artist", "title").first()
    return render(request, "visuals/component_gallery.html", {"product": product})
