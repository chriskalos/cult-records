from .access import (
    can_access_admin_panel,
    can_add_products,
    can_delete_products,
    can_delete_reviews,
    can_edit_products,
    can_manage_bundles,
    can_manage_users,
    can_moderate_reviews,
)


def admin_capabilities(request):
    user = request.user
    return {
        "admin_panel_access": can_access_admin_panel(user),
        "admin_can_manage_users": can_manage_users(user),
        "admin_can_add_products": can_add_products(user),
        "admin_can_edit_products": can_edit_products(user),
        "admin_can_delete_products": can_delete_products(user),
        "admin_can_manage_bundles": can_manage_bundles(user),
        "admin_can_moderate_reviews": can_moderate_reviews(user),
        "admin_can_delete_reviews": can_delete_reviews(user),
    }
