from django.test import TestCase
from django.urls import reverse


class SearchPageTests(TestCase):
    def test_search_page_is_publicly_available(self):
        response = self.client.get(reverse("search:results"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "search/results.html")
