from decimal import Decimal

from django.db import migrations, models


PLACEHOLDER_PRODUCT_IDS = ["PLHLP01", "PLHCD02", "PLHBNDL03", "PLHMRCH04"]

PLACEHOLDER_PRODUCTS = [
    {
        "product_id": "PLHLP01",
        "artist": "Placeholder Artist 1",
        "title": "Placeholder Title 1",
        "description": "Placeholder Description 1",
        "product_type": "LP",
        "price": Decimal("19.99"),
    },
    {
        "product_id": "PLHCD02",
        "artist": "Placeholder Artist 2",
        "title": "Placeholder Title 2",
        "description": "Placeholder Description 2",
        "product_type": "CD",
        "price": Decimal("29.99"),
    },
    {
        "product_id": "PLHBNDL03",
        "artist": "Placeholder Artist 3",
        "title": "Placeholder Title 3",
        "description": "Placeholder Description 3",
        "product_type": "BUNDLE",
        "price": Decimal("39.99"),
    },
    {
        "product_id": "PLHMRCH04",
        "artist": "Placeholder Artist 4",
        "title": "Placeholder Title 4",
        "description": "Placeholder Description 4",
        "product_type": "MERCH",
        "price": Decimal("49.99"),
    },
]

CATALOGUE_PRODUCTS = [
    {
        "product_id": "CLXYZCD",
        "image": "home/images/products/cursed-locale-chriskalos-dot-xyz.jpg",
        "artist": "cursed locale",
        "title": "chriskalos dot xyz",
        "description": "chriskalos dot xyz by cursed locale on CD.",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "CLDANCECD",
        "image": "home/images/products/cursed-locale-dance-w-me.jpg",
        "artist": "cursed locale",
        "title": "dance w me",
        "description": "dance w me by cursed locale on CD.",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "CLHEATCD",
        "image": "home/images/products/cursed-locale-heatwave.jpg",
        "artist": "cursed locale",
        "title": "heatwave",
        "description": "heatwave by cursed locale on CD.",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "MDEVCTRYLP",
        "image": "home/images/products/madeon-victory.jpg",
        "artist": "Madeon",
        "title": "Victory",
        "description": "Madeon's 2026 album Victory on vinyl LP.",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "MDEVCTRYCD",
        "image": "home/images/products/madeon-victory.jpg",
        "artist": "Madeon",
        "title": "Victory",
        "description": "Madeon's 2026 album Victory on CD.",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "MDNC2LP",
        "image": "home/images/products/madonna-confessions-ii.jpg",
        "artist": "Madonna",
        "title": "Confessions II",
        "description": "Madonna's 2026 studio album Confessions II on vinyl LP.",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "MDNC2CD",
        "image": "home/images/products/madonna-confessions-ii.jpg",
        "artist": "Madonna",
        "title": "Confessions II",
        "description": "Madonna's 2026 studio album Confessions II on CD.",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "BBPRTLLP",
        "image": "home/images/products/balu-brigada-portal.jpg",
        "artist": "Balu Brigada",
        "title": "Portal",
        "description": "Balu Brigada's 2025 debut studio album Portal on vinyl LP.",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "BBPRTLCD",
        "image": "home/images/products/balu-brigada-portal.jpg",
        "artist": "Balu Brigada",
        "title": "Portal",
        "description": "Balu Brigada's 2025 debut studio album Portal on CD.",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "RAWYNSLP",
        "image": "home/images/products/rick-astley-whenever-you-need-somebody.jpg",
        "artist": "Rick Astley",
        "title": "Whenever You Need Somebody",
        "description": "Rick Astley's 1987 debut studio album on vinyl LP.",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "RAWYNSCD",
        "image": "home/images/products/rick-astley-whenever-you-need-somebody.jpg",
        "artist": "Rick Astley",
        "title": "Whenever You Need Somebody",
        "description": "Rick Astley's 1987 debut studio album on CD.",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
]


def populate_catalogue(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    Product.objects.filter(product_id__in=PLACEHOLDER_PRODUCT_IDS).delete()
    Product.objects.bulk_create(Product(**data) for data in CATALOGUE_PRODUCTS)


def restore_placeholders(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    Product.objects.filter(
        product_id__in=[product["product_id"] for product in CATALOGUE_PRODUCTS]
    ).delete()
    Product.objects.bulk_create(Product(**data) for data in PLACEHOLDER_PRODUCTS)


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0003_use_string_product_ids"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="image",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.RunPython(populate_catalogue, restore_placeholders),
    ]
