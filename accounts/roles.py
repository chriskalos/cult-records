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

