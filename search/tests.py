from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from home.models import Product

from .forms import SearchForm
from .services import search_products


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


class ProductSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.madonna_lp = Product.objects.create(
            product_id="MDNCLP",
            artist="Madonna",
            title="Confessions on a Dance Floor",
            description="A dance-pop album",
            product_type=Product.ProductType.LP,
            price=Decimal("39.99"),
        )
        cls.madonna_cd = Product.objects.create(
            product_id="MDNACD",
            artist="Madonna",
            title="American Life",
            description="A studio album",
            product_type=Product.ProductType.CD,
            price=Decimal("19.99"),
        )

    def test_keyword_matches_title_artist_or_description(self):
        title_results = search_products({"query": "confessions"})
        artist_results = search_products({"query": "madonna"})
        description_results = search_products({"query": "dance-pop"})

        self.assertIn(self.madonna_lp, title_results)
        self.assertIn(self.madonna_lp, artist_results)
        self.assertIn(self.madonna_lp, description_results)

    def test_words_can_match_across_artist_and_title(self):
        results = search_products({"query": "madonna confessions"})

        self.assertIn(self.madonna_lp, results)

    def test_word_order_does_not_prevent_a_match(self):
        results = search_products({"query": "confessions madonna"})

        self.assertIn(self.madonna_lp, results)

    def test_reasonable_misspellings_return_relevant_product(self):
        results = search_products({"query": "madona confesions"})

        self.assertIn(self.madonna_lp, results)

    def test_unrelated_query_does_not_return_weak_matches(self):
        results = search_products({"query": "zzzz unrelated"})

        self.assertEqual(results, [])

    def test_exact_match_ranks_above_fuzzy_match(self):
        fuzzy_product = Product.objects.create(
            product_id="MDNTRBT",
            artist="Madona Tribute",
            title="Live",
            description="A tribute performance",
            product_type=Product.ProductType.CD,
            price=Decimal("14.99"),
        )

        results = search_products({"query": "Madonna"})

        self.assertLess(results.index(self.madonna_lp), results.index(fuzzy_product))

    def test_artist_and_title_match_ranks_above_description_match(self):
        description_match = Product.objects.create(
            product_id="POPDOC",
            artist="Various Artists",
            title="Pop Documentary",
            description="A documentary about Madonna and Confessions",
            product_type=Product.ProductType.CD,
            price=Decimal("12.99"),
        )

        results = search_products({"query": "madonna confessions"})

        self.assertLess(results.index(self.madonna_lp), results.index(description_match))

    def test_filters_can_be_combined(self):
        results = search_products(
            {
                "artist": "Madonna",
                "product_type": Product.ProductType.LP,
                "min_price": Decimal("30.00"),
                "max_price": Decimal("40.00"),
            }
        )

        self.assertIn(self.madonna_lp, results)
        self.assertNotIn(self.madonna_cd, results)

    def test_product_type_filter_works_without_keyword(self):
        results = search_products({"product_type": Product.ProductType.CD})

        self.assertIn(self.madonna_cd, results)
        self.assertNotIn(self.madonna_lp, results)

    def test_price_filter_boundaries_are_inclusive(self):
        results = search_products(
            {
                "min_price": Decimal("39.99"),
                "max_price": Decimal("39.99"),
            }
        )

        self.assertIn(self.madonna_lp, results)
        self.assertNotIn(self.madonna_cd, results)


class SearchPageTests(TestCase):
    def test_search_page_is_publicly_available(self):
        response = self.client.get(reverse("search:results"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search/results.html")
        self.assertIsInstance(response.context["form"], SearchForm)
        self.assertIsNone(response.context["products"])
        self.assertContains(response, "data-search-form")
        self.assertContains(response, 'data-live-filter="immediate"', count=2)
        self.assertContains(response, 'data-live-filter="debounced"', count=2)
        self.assertContains(response, "/static/search/js/filters.js")

    def test_valid_search_displays_matching_products(self):
        response = self.client.get(
            reverse("search:results"),
            {"query": "Placeholder Title 2"},
        )

        self.assertContains(response, "Placeholder Artist 2")
        self.assertContains(response, "Placeholder Title 2")
        self.assertEqual(response.context["products"][0].product_id, "PLHCD02")
        self.assertTemplateUsed(response, "home/includes/product_card.html")

    def test_search_page_displays_result_count(self):
        response = self.client.get(
            reverse("search:results"),
            {"artist": "Placeholder Artist 2"},
        )

        self.assertContains(response, "1 result")

    def test_search_page_displays_empty_state(self):
        response = self.client.get(
            reverse("search:results"),
            {"query": "zzzz unrelated"},
        )

        self.assertContains(response, "No products matched your search.")

    def test_header_search_preserves_current_query(self):
        response = self.client.get(
            reverse("search:results"),
            {"query": "madona confesions"},
        )

        self.assertContains(response, 'value="madona confesions"', count=2)

    def test_invalid_price_range_does_not_run_search(self):
        response = self.client.get(
            reverse("search:results"),
            {"min_price": "30", "max_price": "20"},
        )

        self.assertIsNone(response.context["products"])
        self.assertContains(
            response,
            "Maximum price must be greater than or equal to minimum price.",
        )
