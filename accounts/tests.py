from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase

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
