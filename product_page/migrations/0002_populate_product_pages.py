from django.db import migrations


def populate_product_pages(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    ProductPage = apps.get_model("product_page", "ProductPage")

    ProductPage.objects.bulk_create(
        ProductPage(product=product, long_description=product.description)
        for product in Product.objects.all()
    )


def clear_product_pages(apps, schema_editor):
    ProductPage = apps.get_model("product_page", "ProductPage")
    ProductPage.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("product_page", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(populate_product_pages, clear_product_pages),
    ]
