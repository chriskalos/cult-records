from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .audit import record_admin_activity
from .models import AdminActivity


class AdminPanelAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.get(username="admin")
        self.editor = User.objects.get(username="editor")
        self.user = User.objects.get(username="user1")
        self.dashboard_url = reverse("admin_panel:dashboard")

    def test_custom_panel_uses_the_conventional_admin_url(self):
        self.assertEqual(self.dashboard_url, "/admin/")
        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)

    def test_anonymous_visitors_are_sent_to_sign_in(self):
        response = self.client.get(self.dashboard_url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={self.dashboard_url}",
        )

    def test_regular_users_cannot_access_the_panel(self):
        self.client.force_login(self.user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 403)

    def test_admins_and_editors_can_access_the_dashboard(self):
        for user in (self.admin, self.editor):
            with self.subTest(username=user.username):
                self.client.force_login(user)
                response = self.client.get(self.dashboard_url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "admin_panel/dashboard.html")

    def test_editor_access_is_limited_to_products_reviews_and_activity(self):
        self.client.force_login(self.editor)

        permitted_urls = (
            reverse("admin_panel:products"),
            reverse("admin_panel:reviews"),
            reverse("admin_panel:activity"),
            reverse("admin_panel:visuals"),
        )
        forbidden_urls = (
            reverse("admin_panel:users"),
            reverse("admin_panel:bundles"),
        )

        for url in permitted_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

        for url in forbidden_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_editor_context_does_not_grant_admin_only_actions(self):
        self.client.force_login(self.editor)

        response = self.client.get(self.dashboard_url)

        self.assertTrue(response.context["admin_can_edit_products"])
        self.assertTrue(response.context["admin_can_moderate_reviews"])
        self.assertFalse(response.context["admin_can_add_products"])
        self.assertFalse(response.context["admin_can_delete_products"])
        self.assertFalse(response.context["admin_can_manage_bundles"])
        self.assertFalse(response.context["admin_can_manage_users"])
        self.assertFalse(response.context["admin_can_delete_reviews"])

    def test_admin_can_access_every_foundation_section(self):
        self.client.force_login(self.admin)

        urls = (
            reverse("admin_panel:users"),
            reverse("admin_panel:products"),
            reverse("admin_panel:bundles"),
            reverse("admin_panel:reviews"),
            reverse("admin_panel:activity"),
            reverse("admin_panel:visuals"),
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class AdminPanelPresentationTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin = self.User.objects.get(username="admin")
        self.editor = self.User.objects.get(username="editor")
        self.user = self.User.objects.get(username="user1")

    def test_dashboard_uses_the_admin_shell_and_blueprint_styles(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertContains(response, "admin_panel/css/admin.css")
        self.assertContains(response, 'id="admin-navigation"')
        self.assertContains(response, 'id="admin-main-content"')
        self.assertContains(response, "Cult Records")
        self.assertContains(response, "Admin panel")
        self.assertContains(response, "Moderation queue")
        self.assertContains(response, "Ready for simulated purchase data")

    def test_component_gallery_contains_the_shared_admin_controls(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_panel:visuals"))

        self.assertContains(response, "Blueprint palette")
        self.assertContains(response, "#07111D")
        self.assertContains(response, "Delete permanently")
        self.assertContains(response, "Management table")
        self.assertContains(response, "Form controls")
        self.assertContains(response, "Confirm administrative action")

    def test_sidebar_reflects_admin_and_editor_capabilities(self):
        self.client.force_login(self.editor)
        editor_response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertContains(editor_response, reverse("admin_panel:products"))
        self.assertContains(editor_response, reverse("admin_panel:reviews"))
        self.assertNotContains(editor_response, reverse("admin_panel:users"))
        self.assertNotContains(editor_response, reverse("admin_panel:bundles"))

        self.client.force_login(self.admin)
        admin_response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertContains(admin_response, reverse("admin_panel:users"))
        self.assertContains(admin_response, reverse("admin_panel:bundles"))

    def test_public_account_menu_only_links_authorized_users_to_admin_panel(self):
        self.client.force_login(self.user)
        user_response = self.client.get(reverse("home"))
        self.assertNotContains(user_response, reverse("admin_panel:dashboard"))

        for user in (self.editor, self.admin):
            with self.subTest(username=user.username):
                self.client.force_login(user)
                response = self.client.get(reverse("home"))
                self.assertContains(response, reverse("admin_panel:dashboard"))


class AdminActivityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.get(username="admin")
        self.editor = User.objects.get(username="editor")
        self.admin_entry = record_admin_activity(
            actor=self.admin,
            action=AdminActivity.Action.UPDATE,
            target_type="Product",
            target_identifier="TESTLP",
            target_label="Test record",
            summary="Updated the test record.",
            metadata={"fields": ["price"]},
        )
        self.editor_entry = record_admin_activity(
            actor=self.editor,
            action=AdminActivity.Action.MODERATION,
            target_type="Review",
            target_identifier="42",
            target_label="Review 42",
            summary="Approved review 42.",
        )

    def test_activity_helper_records_structured_audit_data(self):
        self.assertEqual(self.admin_entry.actor, self.admin)
        self.assertEqual(self.admin_entry.action, AdminActivity.Action.UPDATE)
        self.assertEqual(self.admin_entry.target_identifier, "TESTLP")
        self.assertEqual(self.admin_entry.metadata, {"fields": ["price"]})

    def test_admin_can_see_all_activity(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_panel:activity"))

        self.assertContains(response, self.admin_entry.summary)
        self.assertContains(response, self.editor_entry.summary)

    def test_editor_only_sees_their_own_activity(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse("admin_panel:activity"))

        self.assertContains(response, self.editor_entry.summary)
        self.assertNotContains(response, self.admin_entry.summary)

    def test_activity_can_be_filtered_by_action_and_search_text(self):
        self.client.force_login(self.admin)

        action_response = self.client.get(
            reverse("admin_panel:activity"),
            {"action": AdminActivity.Action.MODERATION},
        )
        search_response = self.client.get(
            reverse("admin_panel:activity"),
            {"query": "TESTLP"},
        )

        self.assertContains(action_response, self.editor_entry.summary)
        self.assertNotContains(action_response, self.admin_entry.summary)
        self.assertContains(search_response, self.admin_entry.summary)
        self.assertNotContains(search_response, self.editor_entry.summary)

    def test_dashboard_shows_visible_recent_activity(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertContains(response, self.editor_entry.summary)
        self.assertNotContains(response, self.admin_entry.summary)
