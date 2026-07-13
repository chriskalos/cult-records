from django.db import models


class Product(models.Model):
    class ProductType(models.TextChoices):
        LP = "LP", "LP"
        CD = "CD", "CD"
        BUNDLE = "BUNDLE", "Bundle"
        MERCH = "MERCH", "Merch"

    image = models.URLField(blank=True)
    artist = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    product_type = models.CharField(max_length=6, choices=ProductType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.artist} - {self.title}"
