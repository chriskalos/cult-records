from django.db.models import Q

from home.models import Product


def search_products(criteria):
    products = Product.objects.all()
    query = criteria.get("query", "").strip()

    if query:
        products = products.filter(
            Q(title__icontains=query)
            | Q(artist__icontains=query)
            | Q(description__icontains=query)
        )

    if artist := criteria.get("artist"):
        products = products.filter(artist=artist)

    if product_type := criteria.get("product_type"):
        products = products.filter(product_type=product_type)

    if (min_price := criteria.get("min_price")) is not None:
        products = products.filter(price__gte=min_price)

    if (max_price := criteria.get("max_price")) is not None:
        products = products.filter(price__lte=max_price)

    return products.order_by("artist", "title")
