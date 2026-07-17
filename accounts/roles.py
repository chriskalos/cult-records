from enum import StrEnum


EDITOR_GROUP_NAME = "Editors"


class UserRole(StrEnum):
    ADMIN = "Admin"
    EDITOR = "Editor"
    USER = "User"
    ANONYMOUS = "Anonymous"


def role_for_user(user):
    if not user.is_authenticated:
        return UserRole.ANONYMOUS
    if user.is_superuser:
        return UserRole.ADMIN
    if user.groups.filter(name=EDITOR_GROUP_NAME).exists():
        return UserRole.EDITOR
    return UserRole.USER


def set_user_role(user, role):
    from django.contrib.auth.models import Group

    role = UserRole(role)
    editors, _ = Group.objects.get_or_create(name=EDITOR_GROUP_NAME)

    user.groups.remove(editors)
    user.is_staff = role is UserRole.ADMIN
    user.is_superuser = role is UserRole.ADMIN
    user.save(update_fields=("is_staff", "is_superuser"))

    if role is UserRole.EDITOR:
        user.groups.add(editors)
