from django.core.validators import RegexValidator
from django.db import migrations, models


PLACEHOLDER_PRODUCT_IDS = {
    "Placeholder Title 1": "PLHLP01",
    "Placeholder Title 2": "PLHCD02",
    "Placeholder Title 3": "PLHBNDL03",
    "Placeholder Title 4": "PLHMRCH04",
}


def assign_string_product_ids(apps, schema_editor):
    Product = apps.get_model("home", "Product")

    for product in Product.objects.all():
        old_product_id = str(product.product_id)
        new_product_id = PLACEHOLDER_PRODUCT_IDS.get(
            product.title,
            f"PRD{int(old_product_id):06d}",
        )
        Product.objects.filter(product_id=old_product_id).update(
            product_id=new_product_id
        )


def restore_numeric_product_ids(apps, schema_editor):
    Product = apps.get_model("home", "Product")
    placeholder_ids = {
        product_id: str(index)
        for index, product_id in enumerate(PLACEHOLDER_PRODUCT_IDS.values(), start=1)
    }

    for product in Product.objects.all():
        old_product_id = str(product.product_id)
        if old_product_id in placeholder_ids:
            new_product_id = placeholder_ids[old_product_id]
        else:
            new_product_id = str(int(old_product_id.removeprefix("PRD")))

        Product.objects.filter(product_id=old_product_id).update(
            product_id=new_product_id
        )


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0002_add_placeholder_products"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="id",
            new_name="product_id",
        ),
        migrations.AlterField(
            model_name="product",
            name="product_id",
            field=models.CharField(
                max_length=20,
                primary_key=True,
                serialize=False,
                validators=[
                    RegexValidator(
                        regex="^[A-Z0-9]+$",
                        message="Use only uppercase letters and numbers.",
                    )
                ],
            ),
        ),
        migrations.RunPython(
            assign_string_product_ids,
            restore_numeric_product_ids,
        ),
    ]
