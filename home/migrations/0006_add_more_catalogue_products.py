from decimal import Decimal

from django.db import migrations


PRODUCTS = [
    {
        "product_id": "CPDIWTTYELP",
        "image": "home/images/products/caroline-polachek-desire-everasking-edition.jpg",
        "artist": "Caroline Polachek",
        "title": "Desire, I Want To Turn Into You (Everasking Edition)",
        "description": "Caroline Polachek's 2023 album Desire, I Want To Turn Into You (Everasking Edition) on vinyl LP.",
        "genre": "Indie Pop",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "CPDIWTTYECD",
        "image": "home/images/products/caroline-polachek-desire-everasking-edition.jpg",
        "artist": "Caroline Polachek",
        "title": "Desire, I Want To Turn Into You (Everasking Edition)",
        "description": "Caroline Polachek's 2023 album Desire, I Want To Turn Into You (Everasking Edition) on CD.",
        "genre": "Indie Pop",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "UNDRSCRSULP",
        "image": "home/images/products/underscores-u.jpg",
        "artist": "Underscores",
        "title": "U",
        "description": "Underscores' 2026 album U on vinyl LP.",
        "genre": "Pop",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "UNDRSCRSUCD",
        "image": "home/images/products/underscores-u.jpg",
        "artist": "Underscores",
        "title": "U",
        "description": "Underscores' 2026 album U on CD.",
        "genre": "Pop",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "SGLAHLLP",
        "image": "home/images/products/sg-lewis-audiolust-and-higherlove.jpg",
        "artist": "SG Lewis",
        "title": "AudioLust & HigherLove",
        "description": "SG Lewis' 2023 album AudioLust & HigherLove on vinyl LP.",
        "genre": "Electronic",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "SGLAHLCD",
        "image": "home/images/products/sg-lewis-audiolust-and-higherlove.jpg",
        "artist": "SG Lewis",
        "title": "AudioLust & HigherLove",
        "description": "SG Lewis' 2023 album AudioLust & HigherLove on CD.",
        "genre": "Electronic",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "PRCLSPRCLSLP",
        "image": "home/images/products/parcels-parcels.jpg",
        "artist": "Parcels",
        "title": "Parcels",
        "description": "Parcels' 2018 debut studio album on vinyl LP.",
        "genre": "Alternative",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "PRCLSPRCLSCD",
        "image": "home/images/products/parcels-parcels.jpg",
        "artist": "Parcels",
        "title": "Parcels",
        "description": "Parcels' 2018 debut studio album on CD.",
        "genre": "Alternative",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "KPDTURLP",
        "image": "home/images/products/kim-petras-detour.jpg",
        "artist": "Kim Petras",
        "title": "Detour",
        "description": "Kim Petras' 2026 album Detour on vinyl LP.",
        "genre": "Pop",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "KPDTURCD",
        "image": "home/images/products/kim-petras-detour.jpg",
        "artist": "Kim Petras",
        "title": "Detour",
        "description": "Kim Petras' 2026 album Detour on CD.",
        "genre": "Pop",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "DPRAMLP",
        "image": "home/images/products/daft-punk-random-access-memories.jpg",
        "artist": "Daft Punk",
        "title": "Random Access Memories",
        "description": "Daft Punk's 2013 studio album Random Access Memories on vinyl LP.",
        "genre": "Pop",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "DPRAMCD",
        "image": "home/images/products/daft-punk-random-access-memories.jpg",
        "artist": "Daft Punk",
        "title": "Random Access Memories",
        "description": "Daft Punk's 2013 studio album Random Access Memories on CD.",
        "genre": "Pop",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "SLYWGIAMLP",
        "image": "home/images/products/slayyyter-worst-girl-in-america.jpg",
        "artist": "Slayyyter",
        "title": "WOR$T GIRL IN AMERICA",
        "description": "Slayyyter's 2026 album WOR$T GIRL IN AMERICA on vinyl LP.",
        "genre": "Pop",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "SLYWGIAMCD",
        "image": "home/images/products/slayyyter-worst-girl-in-america.jpg",
        "artist": "Slayyyter",
        "title": "WOR$T GIRL IN AMERICA",
        "description": "Slayyyter's 2026 album WOR$T GIRL IN AMERICA on CD.",
        "genre": "Pop",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "BRKHYPLP",
        "image": "home/images/products/brakence-hypochondriac.jpg",
        "artist": "brakence",
        "title": "hypochondriac",
        "description": "brakence's 2022 album hypochondriac on vinyl LP.",
        "genre": "Alternative",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "BRKHYPCD",
        "image": "home/images/products/brakence-hypochondriac.jpg",
        "artist": "brakence",
        "title": "hypochondriac",
        "description": "brakence's 2022 album hypochondriac on CD.",
        "genre": "Alternative",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
    {
        "product_id": "CSDDLP",
        "image": "home/images/products/callinsick-doubling-down.jpg",
        "artist": "callinsick",
        "title": "Doubling Down",
        "description": "callinsick's 2025 EP Doubling Down on vinyl LP.",
        "genre": "Indie Pop",
        "product_type": "LP",
        "price": Decimal("14.99"),
    },
    {
        "product_id": "CSDDCD",
        "image": "home/images/products/callinsick-doubling-down.jpg",
        "artist": "callinsick",
        "title": "Doubling Down",
        "description": "callinsick's 2025 EP Doubling Down on CD.",
        "genre": "Indie Pop",
        "product_type": "CD",
        "price": Decimal("6.99"),
    },
]


def add_products(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    Product.objects.bulk_create(Product(**data) for data in PRODUCTS)


def remove_products(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    Product.objects.filter(
        product_id__in=[product["product_id"] for product in PRODUCTS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0005_add_product_genre"),
    ]

    operations = [
        migrations.RunPython(add_products, remove_products),
    ]
