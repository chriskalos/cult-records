from django.db import migrations


EDITOR_GROUP_NAME = "Editors"

REMOVED_PERMISSIONS = (
    ("home", "add_product"),
    ("home", "delete_product"),
    ("product_page", "add_productpage"),
    ("product_page", "delete_productpage"),
    ("product_page", "delete_review"),
)


def update_editor_permissions(apps, schema_editor, add_removed_permissions=False):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    try:
        editors = Group.objects.get(name=EDITOR_GROUP_NAME)
    except Group.DoesNotExist:
        return

    permissions = Permission.objects.none()
    for app_label, codename in REMOVED_PERMISSIONS:
        permissions = permissions | Permission.objects.filter(
            content_type__app_label=app_label,
            codename=codename,
        )

    if add_removed_permissions:
        editors.permissions.add(*permissions)
    else:
        editors.permissions.remove(*permissions)


def limit_editor_permissions(apps, schema_editor):
    update_editor_permissions(apps, schema_editor)


def restore_editor_permissions(apps, schema_editor):
    update_editor_permissions(apps, schema_editor, add_removed_permissions=True)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_seed_roles_and_users"),
    ]

    operations = [
        migrations.RunPython(limit_editor_permissions, restore_editor_permissions),
    ]
