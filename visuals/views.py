from django.shortcuts import render

from home.models import Product
from product_page.forms import ReviewForm


def component_gallery(request):
    products = Product.objects.public().order_by("artist", "title")
    context = {
        "cd_product": products.filter(product_type=Product.ProductType.CD).first(),
        "lp_product": products.filter(product_type=Product.ProductType.LP).first(),
        "review_form": ReviewForm(initial={"rating": 4}),
    }
    return render(request, "visuals/component_gallery.html", context)
