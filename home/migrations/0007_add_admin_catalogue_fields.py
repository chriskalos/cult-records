import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import home.models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0006_add_more_catalogue_products"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="is_visible",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AddField(
            model_name="product",
            name="uploaded_image",
            field=models.ImageField(blank=True, upload_to=home.models.product_image_upload_path),
        ),
        migrations.CreateModel(
            name="BundleItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantity",
                    models.PositiveSmallIntegerField(
                        default=1,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "position",
                    models.PositiveSmallIntegerField(
                        default=1,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "bundle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bundle_items",
                        to="home.product",
                    ),
                ),
                (
                    "component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="component_of",
                        to="home.product",
                    ),
                ),
            ],
            options={
                "ordering": ("position", "pk"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("bundle", "component"),
                        name="unique_component_per_bundle",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("quantity__gte", 1)),
                        name="bundle_item_quantity_at_least_one",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("position__gte", 1)),
                        name="bundle_item_position_at_least_one",
                    ),
                ],
            },
        ),
    ]
