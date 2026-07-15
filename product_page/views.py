from django.shortcuts import get_object_or_404, render

from home.models import Product

from .models import ProductPage


def product_detail(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)

    try:
        page = product.page
    except ProductPage.DoesNotExist:
        page = None

    long_description = (
        page.long_description if page and page.long_description else product.description
    )

    return render(
        request,
        "product_page/detail.html",
        {
            "product": product,
            "page": page,
            "long_description": long_description,
        },
    )
