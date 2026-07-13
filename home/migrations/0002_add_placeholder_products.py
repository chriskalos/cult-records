from decimal import Decimal

from django.db import migrations


PLACEHOLDER_PRODUCTS = [
    {
        "artist": "Placeholder Artist 1",
        "title": "Placeholder Title 1",
        "description": "Placeholder Description 1",
        "product_type": "LP",
        "price": Decimal("19.99"),
    },
    {
        "artist": "Placeholder Artist 2",
        "title": "Placeholder Title 2",
        "description": "Placeholder Description 2",
        "product_type": "CD",
        "price": Decimal("29.99"),
    },
    {
        "artist": "Placeholder Artist 3",
        "title": "Placeholder Title 3",
        "description": "Placeholder Description 3",
        "product_type": "BUNDLE",
        "price": Decimal("39.99"),
    },
    {
        "artist": "Placeholder Artist 4",
        "title": "Placeholder Title 4",
        "description": "Placeholder Description 4",
        "product_type": "MERCH",
        "price": Decimal("49.99"),
    },
]


def add_placeholder_products(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    Product.objects.bulk_create(
        Product(**product_data) for product_data in PLACEHOLDER_PRODUCTS
    )


def remove_placeholder_products(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    Product.objects.filter(
        title__in=[product_data["title"] for product_data in PLACEHOLDER_PRODUCTS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            add_placeholder_products,
            remove_placeholder_products,
        ),
    ]
