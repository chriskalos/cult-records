from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Product


class ProductModelTests(TestCase):
    def test_product_stores_catalogue_data(self):
        product = Product.objects.create(
            product_id="MDNC2LP",
            artist="Madeon",
            title="Victory",
            description="Placeholder description for Madeon - Victory LP",
            product_type=Product.ProductType.LP,
            price=Decimal("69.99"),
        )

        product.full_clean()
        self.assertEqual(product.pk, "MDNC2LP")
        self.assertEqual(product.image, "")
        self.assertEqual(product.artist, "Madeon")
        self.assertEqual(product.product_type, "LP")
        self.assertEqual(product.price, Decimal("69.99"))
        self.assertEqual(str(product), "Madeon - Victory")

    def test_product_id_rejects_invalid_characters(self):
        product = Product(
            product_id="invalid-id",
            artist="Placeholder Artist",
            title="Placeholder Title",
            description="Placeholder Description",
            product_type=Product.ProductType.CD,
            price=Decimal("29.99"),
        )

        with self.assertRaises(ValidationError):
            product.full_clean()

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
        self.assertEqual(
            list(products.values_list("product_id", flat=True)),
            ["PLHLP01", "PLHCD02", "PLHBNDL03", "PLHMRCH04"],
        )
