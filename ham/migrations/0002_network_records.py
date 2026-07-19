import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ham", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="HumanAsset",
            fields=[
                ("asset_code", models.CharField(max_length=20, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("alias", models.CharField(max_length=120)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("silent", "Temporarily silent"),
                            ("misplaced", "Misplaced"),
                            ("disputed", "Existence disputed"),
                            ("on_break", "On break"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=12,
                    ),
                ),
                ("location_label", models.CharField(max_length=160)),
                (
                    "latitude",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=9,
                        validators=[
                            django.core.validators.MinValueValidator(-90),
                            django.core.validators.MaxValueValidator(90),
                        ],
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=9,
                        validators=[
                            django.core.validators.MinValueValidator(-180),
                            django.core.validators.MaxValueValidator(180),
                        ],
                    ),
                ),
                ("portrait", models.CharField(max_length=255)),
                ("network_role", models.CharField(max_length=180)),
                ("civilian_cover", models.CharField(max_length=180)),
                ("joined_on", models.DateField()),
                ("last_contact", models.DateField()),
                (
                    "consensus",
                    models.CharField(
                        choices=[
                            ("unanimous", "Unanimous"),
                            ("majority", "Majority"),
                            ("split", "Split"),
                            ("one_guy", "One node insists"),
                        ],
                        max_length=12,
                    ),
                ),
                (
                    "exposure",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("moderate", "Moderate"),
                            ("severe", "Severe"),
                            ("paperwork", "Mostly paperwork"),
                        ],
                        max_length=12,
                    ),
                ),
                ("summary", models.TextField()),
                ("network_notes", models.TextField()),
                ("known_irregularity", models.TextField()),
                ("is_visible", models.BooleanField(db_index=True, default=True)),
            ],
            options={"ordering": ("asset_code",)},
        ),
        migrations.CreateModel(
            name="Directive",
            fields=[
                ("code", models.CharField(max_length=20, primary_key=True, serialize=False)),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("whenever", "Whenever"),
                            ("routine", "Routine"),
                            ("important", "Important"),
                            ("absolute", "Absolutely do this"),
                        ],
                        max_length=10,
                    ),
                ),
                ("instruction", models.TextField()),
                ("rationale", models.TextField()),
                ("status_line", models.CharField(max_length=180)),
                ("position", models.PositiveSmallIntegerField(default=1)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={"ordering": ("position", "code")},
        ),
        migrations.CreateModel(
            name="ArchiveDocument",
            fields=[
                ("code", models.CharField(max_length=20, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=180)),
                ("classification", models.CharField(max_length=80)),
                ("filed_on", models.DateField()),
                ("summary", models.TextField()),
                ("excerpt", models.TextField()),
                (
                    "redaction_level",
                    models.PositiveSmallIntegerField(
                        default=0,
                        validators=[django.core.validators.MaxValueValidator(5)],
                    ),
                ),
                ("is_visible", models.BooleanField(db_index=True, default=True)),
            ],
            options={"ordering": ("-filed_on", "code")},
        ),
        migrations.CreateModel(
            name="AssetObservation",
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
                ("reference", models.CharField(max_length=24, unique=True)),
                ("observed_on", models.DateField()),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("routine", "Routine"),
                            ("warning", "Warning"),
                            ("disputed", "Disputed"),
                            ("admin", "Administrative"),
                        ],
                        max_length=10,
                    ),
                ),
                ("summary", models.TextField()),
                (
                    "asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="observations",
                        to="ham.humanasset",
                    ),
                ),
            ],
            options={"ordering": ("-observed_on", "reference")},
        ),
        migrations.AddConstraint(
            model_name="humanasset",
            constraint=models.CheckConstraint(
                condition=models.Q(("latitude__gte", -90), ("latitude__lte", 90)),
                name="ham_asset_latitude_in_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="humanasset",
            constraint=models.CheckConstraint(
                condition=models.Q(("longitude__gte", -180), ("longitude__lte", 180)),
                name="ham_asset_longitude_in_range",
            ),
        ),
    ]
