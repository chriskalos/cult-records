from pathlib import Path
from uuid import uuid4

from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


def product_image_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"products/{instance.product_id}/{uuid4().hex}{extension}"


class ProductQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_visible=True).exclude(
            product_type=Product.ProductType.BUNDLE,
            bundle_items__component__is_visible=False,
        ).distinct()


class Product(models.Model):
    class ProductType(models.TextChoices):
        LP = "LP", "LP"
        CD = "CD", "CD"
        BUNDLE = "BUNDLE", "Bundle"
        MERCH = "MERCH", "Merch"

    product_id = models.CharField(
        max_length=20,
        primary_key=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9]+$",
                message="Use only uppercase letters and numbers.",
            )
        ],
    )
    image = models.CharField(max_length=500, blank=True)
    uploaded_image = models.ImageField(
        upload_to=product_image_upload_path,
        blank=True,
    )
    artist = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.CharField(max_length=100, blank=True, db_index=True)
    product_type = models.CharField(max_length=6, choices=ProductType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_visible = models.BooleanField(default=True, db_index=True)

    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return f"{self.artist} - {self.title}"

    @property
    def image_url(self):
        if self.uploaded_image:
            return self.uploaded_image.url
        return self.image

    def get_absolute_url(self):
        return reverse("product_page:detail", args=[self.product_id])


class BundleItem(models.Model):
    bundle = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="bundle_items",
    )
    component = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="component_of",
    )
    quantity = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    position = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("bundle", "component"),
                name="unique_component_per_bundle",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="bundle_item_quantity_at_least_one",
            ),
            models.CheckConstraint(
                condition=models.Q(position__gte=1),
                name="bundle_item_position_at_least_one",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.bundle_id and self.bundle.product_type != Product.ProductType.BUNDLE:
            errors["bundle"] = "Bundle items can only belong to Bundle products."
        if self.component_id and self.component.product_type == Product.ProductType.BUNDLE:
            errors["component"] = "Bundles cannot contain other bundles."
        if self.bundle_id and self.component_id and self.bundle_id == self.component_id:
            errors["component"] = "A bundle cannot contain itself."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} × {self.component} in {self.bundle}"
