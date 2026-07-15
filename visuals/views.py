from django.shortcuts import render

from home.models import Product


def component_gallery(request):
    product = Product.objects.order_by("artist", "title").first()
    context = {
        "product": product,
        "footer_motto": "Bringing you the best of music at the best price... If you're willing to pay it.",
    }
    return render(request, "visuals/component_gallery.html", context)
