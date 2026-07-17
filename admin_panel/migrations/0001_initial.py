from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminActivity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("create", "Created"),
                            ("update", "Updated"),
                            ("delete", "Deleted"),
                            ("password", "Changed password"),
                            ("role", "Changed role"),
                            ("visibility", "Changed visibility"),
                            ("moderation", "Moderated"),
                        ],
                        max_length=20,
                    ),
                ),
                ("target_type", models.CharField(max_length=80)),
                ("target_identifier", models.CharField(max_length=255)),
                ("target_label", models.CharField(max_length=255)),
                ("summary", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="admin_activities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-pk"],
            },
        ),
    ]
