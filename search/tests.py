from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from home.models import Product

from .forms import SearchForm


class SearchFormTests(TestCase):
    def test_artist_choices_come_from_catalogue(self):
        Product.objects.create(
            product_id="TESTLP",
            artist="A Test Artist",
            title="Test Album",
            description="Test description",
            product_type=Product.ProductType.LP,
            price=Decimal("24.99"),
        )

        form = SearchForm()

        self.assertIn(("A Test Artist", "A Test Artist"), form.fields["artist"].choices)

    def test_price_range_rejects_maximum_below_minimum(self):
        form = SearchForm({"min_price": "30", "max_price": "20"})

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["max_price"],
            ["Maximum price must be greater than or equal to minimum price."],
        )

    def test_search_filters_are_optional(self):
        form = SearchForm({})

        self.assertTrue(form.is_valid())


class SearchPageTests(TestCase):
    def test_search_page_is_publicly_available(self):
        response = self.client.get(reverse("search:results"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search/results.html")
        self.assertIsInstance(response.context["form"], SearchForm)
