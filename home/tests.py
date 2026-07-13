from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Product


class ProductModelTests(TestCase):
    def test_product_stores_catalogue_data(self):
        product = Product.objects.create(
            artist="Madeon",
            title="Victory",
            description="Placeholder description for Madeon - Victory LP",
            product_type=Product.ProductType.LP,
            price=Decimal("69.99"),
        )

        product.full_clean()
        self.assertEqual(product.image, "")
        self.assertEqual(product.artist, "Madeon")
        self.assertEqual(product.product_type, "LP")
        self.assertEqual(product.price, Decimal("69.99"))
        self.assertEqual(str(product), "Madeon - Victory")

    def test_product_type_choices_are_fixed(self):
        self.assertEqual(
            Product.ProductType.values,
            ["LP", "CD", "BUNDLE", "MERCH"],
        )


class HomePageTests(TestCase):
    def test_home_page_uses_reusable_layout(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/index.html")
        self.assertTemplateUsed(response, "home/base.html")
        self.assertTemplateUsed(response, "home/includes/header.html")
        self.assertTemplateUsed(response, "home/includes/footer.html")

    def test_home_page_displays_products(self):
        response = self.client.get(reverse("home"))

        products = response.context["products"]
        self.assertQuerySetEqual(
            products,
            [
                "Placeholder Title 1",
                "Placeholder Title 2",
                "Placeholder Title 3",
                "Placeholder Title 4",
            ],
            transform=lambda product: product.title,
        )
        self.assertContains(response, "Placeholder Artist 1")
        self.assertContains(response, "Placeholder Description 2")
        self.assertContains(response, "Bundle")
        self.assertContains(response, "49.99€")
