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


def move_portraits_to_cloudinary(apps, schema_editor):
    HumanAsset = apps.get_model("ham", "HumanAsset")
    for asset in HumanAsset.objects.exclude(portrait="").iterator():
        if asset.portrait.startswith(("http://", "https://")):
            continue
        stem = PurePosixPath(asset.portrait).stem
        asset.portrait = _delivery_url(f"cult-records/ham/{stem}")
        asset.save(update_fields=("portrait",))


class Migration(migrations.Migration):
    dependencies = [
        ("ham", "0004_humanasset_uploaded_portrait"),
    ]

    operations = [
        migrations.RunPython(
            move_portraits_to_cloudinary,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
