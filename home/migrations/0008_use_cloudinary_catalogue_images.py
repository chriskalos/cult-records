from pathlib import PurePosixPath
from urllib.parse import quote

from django.conf import settings
from django.db import migrations


def _delivery_url(public_id):
    safe_public_id = quote(public_id, safe="/")
    return (
        f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/"
        f"image/upload/f_auto,q_auto/{safe_public_id}"
    )


def move_catalogue_images_to_cloudinary(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    for product in Product.objects.exclude(image="").iterator():
        if product.image.startswith(("http://", "https://")):
            continue
        stem = PurePosixPath(product.image).stem
        product.image = _delivery_url(f"cult-records/products/{stem}")
        product.save(update_fields=("image",))


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0007_add_admin_catalogue_fields"),
    ]

    operations = [
        migrations.RunPython(
            move_catalogue_images_to_cloudinary,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
