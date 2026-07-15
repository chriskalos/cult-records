from django.core.validators import RegexValidator
from django.db import models


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
    artist = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.CharField(max_length=100, blank=True, db_index=True)
    product_type = models.CharField(max_length=6, choices=ProductType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.artist} - {self.title}"
