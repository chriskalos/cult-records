from django.shortcuts import render

from home.models import Product


def component_gallery(request):
    products = Product.objects.public().order_by("artist", "title")
    context = {
        "cd_product": products.filter(product_type=Product.ProductType.CD).first(),
        "lp_product": products.filter(product_type=Product.ProductType.LP).first(),
    }
    return render(request, "visuals/component_gallery.html", context)
