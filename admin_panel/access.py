from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404

from accounts.roles import EDITOR_GROUP_NAME
from ham.services import user_has_ham_access


def is_editor(user):
    return user.is_authenticated and user.groups.filter(
        name=EDITOR_GROUP_NAME
    ).exists()


def can_access_admin_panel(user):
    return user.is_authenticated and (user.is_superuser or is_editor(user))


def can_manage_users(user):
    return user.is_authenticated and user.is_superuser


def can_add_products(user):
    return user.is_authenticated and user.is_superuser


def can_edit_products(user):
    return user.is_authenticated and (user.is_superuser or is_editor(user))


def can_delete_products(user):
    return user.is_authenticated and user.is_superuser


def can_manage_bundles(user):
    return user.is_authenticated and user.is_superuser


def can_moderate_reviews(user):
    return user.is_authenticated and (user.is_superuser or is_editor(user))


def can_delete_reviews(user):
    return user.is_authenticated and user.is_superuser


def can_manage_human_assets(user):
    return bool(
        user.is_authenticated
        and user.is_superuser
        and user_has_ham_access(user)
    )


def permission_required(check):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not check(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


admin_panel_access_required = permission_required(can_access_admin_panel)
admin_only_required = permission_required(can_manage_users)
product_editor_required = permission_required(can_edit_products)
review_moderator_required = permission_required(can_moderate_reviews)


def enlightened_admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not can_manage_human_assets(request.user):
            raise Http404
        return view_func(request, *args, **kwargs)

    return wrapped
