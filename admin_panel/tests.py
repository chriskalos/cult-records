from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.roles import EDITOR_GROUP_NAME, UserRole, role_for_user
from home.models import Product
from product_page.models import Review

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


class AdminUserManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.get(username="admin")
        self.editor = User.objects.get(username="editor")
        self.user = User.objects.get(username="user1")
        self.client.force_login(self.admin)

    def test_user_list_supports_search_role_and_status_filters(self):
        self.user.email = "listener@example.com"
        self.user.save(update_fields=("email",))

        response = self.client.get(
            reverse("admin_panel:users"),
            {"query": "listener@", "role": UserRole.USER, "status": "active"},
        )

        self.assertContains(response, self.user.username)
        self.assertNotContains(response, self.editor.username)
        self.assertContains(response, "Add user")

    def test_admin_can_create_an_editor_with_a_validated_password(self):
        response = self.client.post(
            reverse("admin_panel:user_create"),
            {
                "username": "catalogue-editor",
                "first_name": "Catalogue",
                "last_name": "Editor",
                "email": "editor@example.com",
                "is_active": "on",
                "role": UserRole.EDITOR,
                "password1": "Secure-editor-password-2026",
                "password2": "Secure-editor-password-2026",
            },
        )

        created = get_user_model().objects.get(username="catalogue-editor")
        self.assertRedirects(
            response,
            reverse("admin_panel:user_edit", args=[created.pk]),
        )
        self.assertTrue(created.check_password("Secure-editor-password-2026"))
        self.assertEqual(role_for_user(created), UserRole.EDITOR)
        self.assertTrue(created.groups.filter(name=EDITOR_GROUP_NAME).exists())
        self.assertFalse(created.is_superuser)
        self.assertTrue(
            AdminActivity.objects.filter(
                action=AdminActivity.Action.CREATE,
                target_identifier=str(created.pk),
            ).exists()
        )

    def test_user_creation_rejects_weak_passwords_and_duplicate_usernames(self):
        response = self.client.post(
            reverse("admin_panel:user_create"),
            {
                "username": "ADMIN",
                "is_active": "on",
                "role": UserRole.USER,
                "password1": "123",
                "password2": "123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertContains(response, "too short")
        self.assertFalse(get_user_model().objects.filter(username="ADMIN").exists())

    def test_admin_can_edit_details_and_assign_a_fixed_role(self):
        response = self.client.post(
            reverse("admin_panel:user_edit", args=[self.user.pk]),
            {
                "username": "renamed-listener",
                "first_name": "Renamed",
                "last_name": "Listener",
                "email": "renamed@example.com",
                "is_active": "on",
                "role": UserRole.EDITOR,
            },
        )

        self.user.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("admin_panel:user_edit", args=[self.user.pk]),
        )
        self.assertEqual(self.user.username, "renamed-listener")
        self.assertEqual(role_for_user(self.user), UserRole.EDITOR)
        self.assertTrue(
            AdminActivity.objects.filter(
                action=AdminActivity.Action.ROLE,
                target_identifier=str(self.user.pk),
            ).exists()
        )

    def test_admin_cannot_change_their_own_role(self):
        response = self.client.post(
            reverse("admin_panel:user_edit", args=[self.admin.pk]),
            {
                "username": self.admin.username,
                "first_name": self.admin.first_name,
                "last_name": self.admin.last_name,
                "email": self.admin.email,
                "is_active": "on",
                "role": UserRole.USER,
            },
        )

        self.admin.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("admin_panel:user_edit", args=[self.admin.pk]),
        )
        self.assertEqual(role_for_user(self.admin), UserRole.ADMIN)

    def test_admin_cannot_deactivate_their_own_account(self):
        response = self.client.post(
            reverse("admin_panel:user_edit", args=[self.admin.pk]),
            {
                "username": self.admin.username,
                "first_name": self.admin.first_name,
                "last_name": self.admin.last_name,
                "email": self.admin.email,
                "role": UserRole.USER,
            },
        )

        self.admin.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot deactivate your own account")
        self.assertTrue(self.admin.is_active)

    def test_admin_can_replace_another_users_password(self):
        response = self.client.post(
            reverse("admin_panel:user_password", args=[self.user.pk]),
            {
                "new_password1": "Replacement-password-2026",
                "new_password2": "Replacement-password-2026",
            },
        )

        self.user.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("admin_panel:user_edit", args=[self.user.pk]),
        )
        self.assertTrue(self.user.check_password("Replacement-password-2026"))
        self.assertTrue(
            AdminActivity.objects.filter(
                action=AdminActivity.Action.PASSWORD,
                target_identifier=str(self.user.pk),
            ).exists()
        )

    def test_user_deletion_is_permanent_and_removes_owned_reviews(self):
        review = Review.objects.create(
            product=Product.objects.get(product_id="MDEVCTRYLP"),
            author=self.user,
            rating=4,
            comment="Delete with account.",
        )
        user_pk = self.user.pk

        response = self.client.post(
            reverse("admin_panel:user_delete", args=[user_pk]),
            {"confirm_username": self.user.username},
        )

        self.assertRedirects(response, reverse("admin_panel:users"))
        self.assertFalse(get_user_model().objects.filter(pk=user_pk).exists())
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())
        self.assertTrue(
            AdminActivity.objects.filter(
                action=AdminActivity.Action.DELETE,
                target_identifier=str(user_pk),
            ).exists()
        )

    def test_admin_cannot_delete_their_own_account(self):
        response = self.client.get(
            reverse("admin_panel:user_delete", args=[self.admin.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(get_user_model().objects.filter(pk=self.admin.pk).exists())

    def test_editor_cannot_access_any_user_management_mutation(self):
        self.client.force_login(self.editor)
        urls = (
            reverse("admin_panel:user_create"),
            reverse("admin_panel:user_edit", args=[self.user.pk]),
            reverse("admin_panel:user_password", args=[self.user.pk]),
            reverse("admin_panel:user_delete", args=[self.user.pk]),
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_user_forms_do_not_expose_django_permission_controls(self):
        response = self.client.get(reverse("admin_panel:user_create"))

        self.assertNotContains(response, "user_permissions")
        self.assertNotContains(response, "Django permissions")
