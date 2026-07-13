from decimal import Decimal

from django.test import TestCase
from django.urls import reverse


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
