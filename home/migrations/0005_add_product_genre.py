from django.db import migrations, models


PRODUCT_GENRES = {
    "CLXYZCD": "Electronic",
    "CLDANCECD": "Electronic",
    "CLHEATCD": "Electronic",
    "MDEVCTRYLP": "Electronic",
    "MDEVCTRYCD": "Electronic",
    "MDNC2LP": "Pop",
    "MDNC2CD": "Pop",
    "BBPRTLLP": "Alternative",
    "BBPRTLCD": "Alternative",
    "RAWYNSLP": "Pop",
    "RAWYNSCD": "Pop",
}


def populate_genres(apps, schema_editor):
    Product = apps.get_model("home", "Product")

    for product_id, genre in PRODUCT_GENRES.items():
        Product.objects.filter(product_id=product_id).update(genre=genre)


def clear_genres(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    Product.objects.filter(product_id__in=PRODUCT_GENRES).update(genre="")


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0004_populate_catalogue"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="genre",
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.RunPython(populate_genres, clear_genres),
    ]
