from io import BytesIO
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from accounts.roles import EDITOR_GROUP_NAME, UserRole, role_for_user
from home.models import BundleItem, Product
from product_page.models import ProductPage, Review

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


class AdminProductManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.get(username="admin")
        self.editor = User.objects.get(username="editor")
        self.product = Product.objects.get(product_id="MDEVCTRYLP")
        self.media_directory = TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

    def _product_data(self, **overrides):
        data = {
            "product_id": "ADMINTESTCD",
            "artist": "Admin Test Artist",
            "title": "Admin Test Album",
            "description": "A short catalogue description.",
            "genre": "Electronic",
            "product_type": Product.ProductType.CD,
            "price": "12.50",
            "is_visible": "on",
            "long_description": "First paragraph.\n\nSecond paragraph.",
            "release_date": "2026-07-17",
            "tracks": "Opening Track\nClosing Track",
        }
        data.update(overrides)
        return data

    def _image_upload(self, name="artwork.png"):
        image_bytes = BytesIO()
        Image.new("RGB", (20, 20), color=(20, 80, 120)).save(
            image_bytes,
            format="PNG",
        )
        return SimpleUploadedFile(
            name,
            image_bytes.getvalue(),
            content_type="image/png",
        )

    def test_product_list_is_searchable_and_role_aware(self):
        self.client.force_login(self.admin)
        admin_response = self.client.get(
            reverse("admin_panel:products"),
            {"query": self.product.product_id, "visibility": "visible"},
        )

        self.assertContains(admin_response, self.product.title)
        self.assertContains(admin_response, "Add product")

        self.client.force_login(self.editor)
        editor_response = self.client.get(reverse("admin_panel:products"))
        self.assertNotContains(editor_response, "Add product")

    def test_admin_can_create_product_with_image_and_product_page_data(self):
        self.client.force_login(self.admin)
        data = self._product_data()
        data["uploaded_image"] = self._image_upload()

        response = self.client.post(
            reverse("admin_panel:product_create"),
            data,
        )

        product = Product.objects.get(product_id="ADMINTESTCD")
        self.assertRedirects(
            response,
            reverse("admin_panel:product_edit", args=[product.product_id]),
        )
        self.assertTrue(product.uploaded_image.name.startswith("products/ADMINTESTCD/"))
        self.assertEqual(product.page.tracks, ["Opening Track", "Closing Track"])
        self.assertEqual(product.page.long_description, "First paragraph.\n\nSecond paragraph.")
        self.assertTrue(
            AdminActivity.objects.filter(
                action=AdminActivity.Action.CREATE,
                target_identifier=product.product_id,
            ).exists()
        )

    def test_product_form_rejects_non_image_upload(self):
        self.client.force_login(self.admin)
        invalid_upload = SimpleUploadedFile(
            "not-an-image.txt",
            b"not an image",
            content_type="text/plain",
        )
        data = self._product_data()
        data["uploaded_image"] = invalid_upload

        response = self.client.post(
            reverse("admin_panel:product_create"),
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid image")
        self.assertFalse(Product.objects.filter(product_id="ADMINTESTCD").exists())

    def test_editor_can_edit_and_hide_existing_product_but_cannot_change_its_id(self):
        self.client.force_login(self.editor)
        edit_data = self._product_data(
            product_id="CHANGEDID",
            artist=self.product.artist,
            title="Edited title",
            description=self.product.description,
            genre=self.product.genre,
            product_type=self.product.product_type,
            price=str(self.product.price),
            long_description=self.product.page.long_description,
            release_date="",
            tracks="",
        )

        edit_response = self.client.post(
            reverse("admin_panel:product_edit", args=[self.product.product_id]),
            edit_data,
        )
        visibility_url = reverse(
            "admin_panel:product_visibility",
            args=[self.product.product_id],
        )
        get_visibility_response = self.client.get(visibility_url)
        hide_response = self.client.post(visibility_url, {"action": "hide"})

        self.product.refresh_from_db()
        self.assertRedirects(
            edit_response,
            reverse("admin_panel:product_edit", args=[self.product.product_id]),
        )
        self.assertEqual(self.product.product_id, "MDEVCTRYLP")
        self.assertEqual(self.product.title, "Edited title")
        self.assertEqual(get_visibility_response.status_code, 405)
        self.assertRedirects(hide_response, reverse("admin_panel:products"))
        self.assertFalse(self.product.is_visible)

    def test_editor_cannot_add_delete_or_edit_bundle_products(self):
        bundle = Product.objects.create(
            product_id="EDITORBUNDLE",
            artist="Cult Records",
            title="Editor bundle",
            description="Bundle.",
            product_type=Product.ProductType.BUNDLE,
            price="20.00",
        )
        self.client.force_login(self.editor)

        self.assertEqual(
            self.client.get(reverse("admin_panel:product_create")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("admin_panel:product_delete", args=[self.product.product_id])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("admin_panel:product_edit", args=[bundle.product_id])
            ).status_code,
            403,
        )

    def test_component_deletion_requires_related_bundle_deletion(self):
        bundle = Product.objects.create(
            product_id="DELETEBUNDLE",
            artist="Cult Records",
            title="Delete bundle",
            description="Bundle.",
            product_type=Product.ProductType.BUNDLE,
            price="20.00",
        )
        BundleItem.objects.create(bundle=bundle, component=self.product)
        self.client.force_login(self.admin)
        delete_url = reverse(
            "admin_panel:product_delete",
            args=[self.product.product_id],
        )

        blocked_response = self.client.post(
            delete_url,
            {"confirm_product_id": self.product.product_id},
        )

        self.assertEqual(blocked_response.status_code, 200)
        self.assertContains(blocked_response, "Delete those bundles with it or cancel")
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.assertTrue(Product.objects.filter(pk=bundle.pk).exists())

        delete_response = self.client.post(
            delete_url,
            {
                "confirm_product_id": self.product.product_id,
                "delete_related_bundles": "on",
            },
        )

        self.assertRedirects(delete_response, reverse("admin_panel:products"))
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
        self.assertFalse(Product.objects.filter(pk=bundle.pk).exists())

    def test_product_deletion_removes_product_page_and_reviews(self):
        review = Review.objects.create(
            product=self.product,
            author=get_user_model().objects.get(username="user1"),
            rating=5,
        )
        page_pk = self.product.page.pk
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:product_delete", args=[self.product.product_id]),
            {"confirm_product_id": self.product.product_id},
        )

        self.assertRedirects(response, reverse("admin_panel:products"))
        self.assertFalse(ProductPage.objects.filter(pk=page_pk).exists())
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())


class AdminBundleManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.get(username="admin")
        self.editor = User.objects.get(username="editor")
        self.component = Product.objects.get(product_id="MDEVCTRYLP")
        self.second_component = Product.objects.exclude(
            product_type=Product.ProductType.BUNDLE,
        ).exclude(pk=self.component.pk).first()

    def _bundle_data(self, **overrides):
        data = {
            "product_id": "ADMINBUNDLE",
            "artist": "Cult Records",
            "title": "Admin bundle",
            "description": "A fixed set of catalogue products.",
            "genre": "Various",
            "price": "39.00",
            "is_visible": "on",
            "long_description": "Everything included in one package.",
            "release_date": "",
            "tracks": "",
            "components-TOTAL_FORMS": "2",
            "components-INITIAL_FORMS": "0",
            "components-MIN_NUM_FORMS": "0",
            "components-MAX_NUM_FORMS": "1000",
            "components-0-component": self.component.pk,
            "components-0-quantity": "2",
            "components-0-position": "1",
            "components-1-component": self.second_component.pk,
            "components-1-quantity": "1",
            "components-1-position": "2",
        }
        data.update(overrides)
        return data

    def test_admin_can_create_bundle_from_existing_non_bundle_products(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("admin_panel:bundle_create"),
            self._bundle_data(),
        )

        bundle = Product.objects.get(pk="ADMINBUNDLE")
        self.assertRedirects(
            response,
            reverse("admin_panel:bundle_edit", args=[bundle.pk]),
        )


        self.assertEqual(bundle.product_type, Product.ProductType.BUNDLE)
        self.assertEqual(
            list(
                bundle.bundle_items.values_list(
                    "component_id",
                    "quantity",
                    "position",
                )
            ),
            [
                (self.component.pk, 2, 1),
                (self.second_component.pk, 1, 2),
            ],
        )
        self.assertTrue(
            AdminActivity.objects.filter(
                action=AdminActivity.Action.CREATE,
                target_type="Bundle",
                target_identifier=bundle.pk,
            ).exists()
        )

    def test_bundle_builder_requires_at_least_one_component(self):
        self.client.force_login(self.admin)
        data = self._bundle_data(
            **{
                "components-TOTAL_FORMS": "1",
                "components-0-component": "",
                "components-0-quantity": "1",
                "components-0-position": "1",
            }
        )
        for key in (
            "components-1-component",
            "components-1-quantity",
            "components-1-position",
        ):
            data.pop(key, None)

        response = self.client.post(reverse("admin_panel:bundle_create"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A bundle must contain at least one product")
        self.assertFalse(Product.objects.filter(pk="ADMINBUNDLE").exists())

    def test_bundle_builder_rejects_nested_bundles(self):
        nested = Product.objects.create(
            product_id="NESTEDSOURCE",
            artist="Cult Records",
            title="Existing bundle",
            description="Cannot be nested.",
            product_type=Product.ProductType.BUNDLE,
            price="20.00",
        )
        self.client.force_login(self.admin)
        data = self._bundle_data(
            **{
                "components-TOTAL_FORMS": "1",
                "components-0-component": nested.pk,
                "components-0-quantity": "1",
                "components-0-position": "1",
            }
        )
        for key in (
            "components-1-component",
            "components-1-quantity",
            "components-1-position",
        ):
            data.pop(key, None)

        response = self.client.post(reverse("admin_panel:bundle_create"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice")
        self.assertFalse(Product.objects.filter(pk="ADMINBUNDLE").exists())

    def test_bundle_contents_are_linked_on_the_public_product_page(self):
        bundle = Product.objects.create(
            product_id="PUBLICBUNDLE",
            artist="Cult Records",
            title="Public bundle",
            description="A public set.",
            product_type=Product.ProductType.BUNDLE,
            price="25.00",
        )
        BundleItem.objects.create(
            bundle=bundle,
            component=self.component,
            quantity=2,
            position=1,
        )

        response = self.client.get(bundle.get_absolute_url())

        self.assertContains(response, "Bundle contents")
        self.assertContains(response, f"2 × {self.component.title}")
        self.assertContains(response, self.component.get_absolute_url())

    def test_editors_cannot_list_create_or_edit_bundles(self):
        bundle = Product.objects.create(
            product_id="ADMINONLYBUNDLE",
            artist="Cult Records",
            title="Admin only",
            description="Bundle.",
            product_type=Product.ProductType.BUNDLE,
            price="20.00",
        )
        self.client.force_login(self.editor)

        urls = (
            reverse("admin_panel:bundles"),
            reverse("admin_panel:bundle_create"),
            reverse("admin_panel:bundle_edit", args=[bundle.pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_admin_product_edit_redirects_bundles_to_the_bundle_builder(self):
        bundle = Product.objects.create(
            product_id="REDIRECTBUNDLE",
            artist="Cult Records",
            title="Redirect bundle",
            description="Bundle.",
            product_type=Product.ProductType.BUNDLE,
            price="20.00",
        )
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("admin_panel:product_edit", args=[bundle.pk])
        )

        self.assertRedirects(
            response,
            reverse("admin_panel:bundle_edit", args=[bundle.pk]),
        )


class AdminReviewManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.get(username="admin")
        self.editor = User.objects.get(username="editor")
        self.regular_user = User.objects.get(username="user1")
        self.product = Product.objects.get(product_id="MDEVCTRYLP")
        self.pending = Review.objects.create(
            product=self.product,
            author=self.regular_user,
            rating=4,
            comment="Pending moderation comment.",
        )
        self.approved = Review.objects.create(
            product=self.product,
            author=User.objects.get(username="user2"),
            rating=5,
            comment="Approved moderation comment.",
            status=Review.Status.APPROVED,
        )
        self.rejected = Review.objects.create(
            product=self.product,
            author=User.objects.get(username="user3"),
            rating=2,
            comment="Rejected moderation comment.",
            status=Review.Status.REJECTED,
            rejection_reason="Original rejection reason.",
        )

    def test_review_list_defaults_to_the_pending_queue_and_supports_filters(self):
        self.client.force_login(self.editor)

        pending_response = self.client.get(reverse("admin_panel:reviews"))
        approved_response = self.client.get(
            reverse("admin_panel:reviews"),
            {"status": Review.Status.APPROVED, "query": "Approved moderation"},
        )

        self.assertContains(pending_response, "Pending moderation comment.")
        self.assertNotContains(pending_response, "Approved moderation comment.")
        self.assertContains(approved_response, "Approved moderation comment.")
        self.assertNotContains(approved_response, "Pending moderation comment.")

    def test_editor_can_approve_or_reject_a_review_and_creates_an_audit_entry(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("admin_panel:review_detail", args=[self.pending.pk]),
            {
                "status": Review.Status.REJECTED,
                "rejection_reason": "  Please add specific details.  ",
            },
        )

        self.pending.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("admin_panel:review_detail", args=[self.pending.pk]),
        )
        self.assertEqual(self.pending.status, Review.Status.REJECTED)
        self.assertEqual(
            self.pending.rejection_reason,
            "Please add specific details.",
        )
        self.assertTrue(
            AdminActivity.objects.filter(
                actor=self.editor,
                action=AdminActivity.Action.MODERATION,
                target_identifier=str(self.pending.pk),
            ).exists()
        )

    def test_approving_a_rejected_review_clears_its_reason(self):
        self.client.force_login(self.editor)

        self.client.post(
            reverse("admin_panel:review_detail", args=[self.rejected.pk]),
            {
                "status": Review.Status.APPROVED,
                "rejection_reason": "Must be cleared.",
            },
        )

        self.rejected.refresh_from_db()
        self.assertEqual(self.rejected.status, Review.Status.APPROVED)
        self.assertEqual(self.rejected.rejection_reason, "")

    def test_editor_can_bulk_moderate_selected_reviews(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("admin_panel:review_bulk_moderate"),
            {
                "selected_reviews": [self.pending.pk, self.rejected.pk],
                "action": Review.Status.APPROVED,
                "rejection_reason": "Ignored for approval.",
            },
        )

        self.pending.refresh_from_db()
        self.rejected.refresh_from_db()
        self.assertRedirects(response, reverse("admin_panel:reviews"))
        self.assertEqual(self.pending.status, Review.Status.APPROVED)
        self.assertEqual(self.rejected.status, Review.Status.APPROVED)
        self.assertEqual(self.rejected.rejection_reason, "")
        self.assertEqual(
            AdminActivity.objects.filter(
                actor=self.editor,
                action=AdminActivity.Action.MODERATION,
                metadata__bulk=True,
            ).count(),
            2,
        )

    def test_bulk_moderation_requires_a_selected_review(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("admin_panel:review_bulk_moderate"),
            {"action": Review.Status.APPROVED},
            follow=True,
        )

        self.pending.refresh_from_db()
        self.assertContains(response, "Select at least one review")
        self.assertEqual(self.pending.status, Review.Status.PENDING)

    def test_only_admins_can_permanently_delete_reviews(self):
        delete_url = reverse("admin_panel:review_delete", args=[self.pending.pk])
        self.client.force_login(self.editor)

        self.assertEqual(self.client.get(delete_url).status_code, 403)

        self.client.force_login(self.admin)
        blocked_response = self.client.post(
            delete_url,
            {"confirm_review_id": "wrong"},
        )
        self.assertEqual(blocked_response.status_code, 200)
        self.assertContains(blocked_response, "does not match")
        self.assertTrue(Review.objects.filter(pk=self.pending.pk).exists())

        deleted_response = self.client.post(
            delete_url,
            {"confirm_review_id": str(self.pending.pk)},
        )
        self.assertRedirects(deleted_response, reverse("admin_panel:reviews"))
        self.assertFalse(Review.objects.filter(pk=self.pending.pk).exists())
        self.assertTrue(
            AdminActivity.objects.filter(
                actor=self.admin,
                action=AdminActivity.Action.DELETE,
                target_identifier=str(self.pending.pk),
            ).exists()
        )

    def test_editor_review_screen_does_not_offer_deletion(self):
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse("admin_panel:review_detail", args=[self.pending.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Delete review")
