from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase
from django.urls import reverse

from .roles import EDITOR_GROUP_NAME, UserRole, role_for_user


class SeededAccountTests(TestCase):
    def test_default_accounts_can_authenticate(self):
        User = get_user_model()
        credentials = {
            "admin": "admin",
            "editor": "editor",
            **{f"user{number}": f"user{number}" for number in range(1, 6)},
        }

        for username, password in credentials.items():
            with self.subTest(username=username):
                user = User.objects.get(username=username)
                self.assertTrue(user.check_password(password))

    def test_default_accounts_have_the_expected_roles(self):
        User = get_user_model()

        self.assertEqual(role_for_user(AnonymousUser()), UserRole.ANONYMOUS)
        self.assertEqual(role_for_user(User.objects.get(username="admin")), UserRole.ADMIN)
        self.assertEqual(
            role_for_user(User.objects.get(username="editor")),
            UserRole.EDITOR,
        )
        self.assertEqual(role_for_user(User.objects.get(username="user1")), UserRole.USER)

    def test_editor_receives_catalogue_and_moderation_permissions(self):
        editor = get_user_model().objects.get(username="editor")

        self.assertTrue(editor.has_perm("home.add_product"))
        self.assertTrue(editor.has_perm("home.change_product"))
        self.assertTrue(editor.has_perm("home.delete_product"))
        self.assertTrue(editor.has_perm("product_page.change_review"))
        self.assertTrue(editor.has_perm("product_page.delete_review"))
        self.assertFalse(editor.has_perm("auth.change_user"))
        self.assertFalse(editor.has_perm("product_page.add_review"))

    def test_regular_users_do_not_receive_management_permissions(self):
        user = get_user_model().objects.get(username="user1")

        self.assertFalse(user.has_perm("home.change_product"))
        self.assertFalse(user.has_perm("product_page.delete_review"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_editor_group_exists(self):
        self.assertTrue(Group.objects.filter(name=EDITOR_GROUP_NAME).exists())


class RegistrationTests(TestCase):
    def test_registration_page_collects_only_username_and_passwords(self):
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["form"].fields),
            ["username", "password1", "password2"],
        )
        self.assertContains(response, "Create account")

    def test_registration_creates_and_signs_in_a_regular_user(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new-listener",
                "password1": "A-secure-password-2026",
                "password2": "A-secure-password-2026",
            },
        )

        user = get_user_model().objects.get(username="new-listener")
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertEqual(role_for_user(user), UserRole.USER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registration_rejects_case_insensitive_duplicate_username(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "ADMIN",
                "password1": "A-secure-password-2026",
                "password2": "A-secure-password-2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertFalse(get_user_model().objects.filter(username="ADMIN").exists())

    def test_registration_applies_django_password_validation(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "weak-password-user",
                "password1": "123",
                "password2": "123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "too short")
        self.assertFalse(
            get_user_model().objects.filter(username="weak-password-user").exists()
        )


class LoginAndLogoutTests(TestCase):
    def test_default_user_can_sign_in(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "user1", "password": "user1"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            get_user_model().objects.get(username="user1").pk,
        )

    def test_login_honours_safe_next_destination(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "user1",
                "password": "user1",
                "next": reverse("search:results"),
            },
        )

        self.assertRedirects(response, reverse("search:results"))

    def test_login_rejects_external_next_destination(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "user1",
                "password": "user1",
                "next": "https://example.com/unsafe",
            },
        )

        self.assertRedirects(response, reverse("home"))

    def test_logout_requires_post_and_clears_the_session(self):
        self.client.login(username="user1", password="user1")

        get_response = self.client.get(reverse("accounts:logout"))
        post_response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_header_changes_with_authentication_state(self):
        anonymous_response = self.client.get(reverse("home"))

        self.assertContains(anonymous_response, "Sign in")
        self.assertContains(anonymous_response, "Register")
        self.assertNotContains(anonymous_response, "Sign out")

        self.client.login(username="user1", password="user1")
        authenticated_response = self.client.get(reverse("home"))

        self.assertContains(authenticated_response, "user1")
        self.assertContains(authenticated_response, "Sign out")
        self.assertNotContains(authenticated_response, ">Register</a>")
