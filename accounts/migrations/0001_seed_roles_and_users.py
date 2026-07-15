from django.contrib.auth.hashers import make_password
from django.db import migrations


EDITOR_GROUP_NAME = "Editors"


def create_permission(Permission, ContentType, app_label, model, action):
    content_type, _ = ContentType.objects.get_or_create(
        app_label=app_label,
        model=model,
    )
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=f"{action}_{model}",
        defaults={"name": f"Can {action} {model}"},
    )
    return permission


def seed_roles_and_users(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    editors, _ = Group.objects.get_or_create(name=EDITOR_GROUP_NAME)

    permission_map = {
        ("home", "product"): ("add", "change", "delete", "view"),
        ("product_page", "productpage"): ("add", "change", "delete", "view"),
        ("product_page", "review"): ("change", "delete", "view"),
    }
    for (app_label, model), actions in permission_map.items():
        for action in actions:
            editors.permissions.add(
                create_permission(
                    Permission,
                    ContentType,
                    app_label,
                    model,
                    action,
                )
            )

    admin, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "password": make_password("admin"),
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if not created:
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.save(update_fields=("is_active", "is_staff", "is_superuser"))

    editor, _ = User.objects.get_or_create(
        username="editor",
        defaults={
            "password": make_password("editor"),
            "is_active": True,
        },
    )
    editor.groups.add(editors)

    for number in range(1, 6):
        username = f"user{number}"
        User.objects.get_or_create(
            username=username,
            defaults={
                "password": make_password(username),
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("home", "0005_add_product_genre"),
        ("product_page", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles_and_users, migrations.RunPython.noop),
    ]

