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
        self.assertEqual(len(products), 4)
        self.assertEqual(
            products[0],
            {
                "image": None,
                "title": "Madeon - Victory LP",
                "description": "Placeholder description for Madeon - Victory LP",
                "price": Decimal("69.99"),
            },
        )
        self.assertContains(response, "Madonna - Confessions II LP")
        self.assertContains(response, "Porter Robinson - Smile LP")
        self.assertContains(response, "Secret Unreleased Daft Punk LP")
        self.assertContains(response, "420.00€")
