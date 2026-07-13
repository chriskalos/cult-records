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
        self.assertContains(response, "Hello World!")
