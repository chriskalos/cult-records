import django.core.validators
import django.db.models.deletion
import product_page.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("home", "0005_add_product_genre"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductPage",
            fields=[
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="page",
                        serialize=False,
                        to="home.product",
                    ),
                ),
                ("long_description", models.TextField(blank=True)),
                ("release_date", models.DateField(blank=True, null=True)),
                (
                    "tracks",
                    models.JSONField(
                        blank=True,
                        default=list,
                        validators=[product_page.models.validate_track_list],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Review",
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
                    "rating",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ]
                    ),
                ),
                (
                    "comment",
                    models.TextField(
                        blank=True,
                        max_length=2000,
                        validators=[django.core.validators.MaxLengthValidator(2000)],
                    ),
                ),
                ("is_approved", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="home.product",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-pk"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("product", "author"),
                        name="one_review_per_product_author",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("rating__gte", 1), ("rating__lte", 5)),
                        name="review_rating_between_1_and_5",
                    ),
                ],
            },
        ),
    ]
