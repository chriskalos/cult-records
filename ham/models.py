from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def human_asset_portrait_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"ham/assets/{instance.asset_code}/{uuid4().hex}{extension}"


class HamClearance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ham_clearance",
    )
    is_enlightened = models.BooleanField(default=False, db_index=True)
    enlightened_at = models.DateTimeField(blank=True, null=True)
    source_order = models.ForeignKey(
        "cart.Order",
        on_delete=models.SET_NULL,
        related_name="granted_ham_clearances",
        blank=True,
        null=True,
    )

    def __str__(self):
        state = "enlightened" if self.is_enlightened else "unaware"
        return f"{self.user} ({state})"


class HumanAsset(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SILENT = "silent", "Temporarily silent"
        MISPLACED = "misplaced", "Misplaced"
        DISPUTED = "disputed", "Existence disputed"
        ON_BREAK = "on_break", "On break"

    class Consensus(models.TextChoices):
        UNANIMOUS = "unanimous", "Unanimous"
        MAJORITY = "majority", "Majority"
        SPLIT = "split", "Split"
        ONE_GUY = "one_guy", "One node insists"

    class Exposure(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        SEVERE = "severe", "Severe"
        PAPERWORK = "paperwork", "Mostly paperwork"

    asset_code = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=120)
    alias = models.CharField(max_length=120)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    location_label = models.CharField(max_length=160)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    portrait = models.CharField(max_length=255, blank=True)
    uploaded_portrait = models.ImageField(
        upload_to=human_asset_portrait_upload_path,
        blank=True,
    )
    network_role = models.CharField(max_length=180)
    civilian_cover = models.CharField(max_length=180)
    joined_on = models.DateField()
    last_contact = models.DateField()
    consensus = models.CharField(max_length=12, choices=Consensus.choices)
    exposure = models.CharField(max_length=12, choices=Exposure.choices)
    summary = models.TextField()
    network_notes = models.TextField()
    known_irregularity = models.TextField()
    is_visible = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("asset_code",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(latitude__gte=-90, latitude__lte=90),
                name="ham_asset_latitude_in_range",
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__gte=-180, longitude__lte=180),
                name="ham_asset_longitude_in_range",
            ),
        ]

    def __str__(self):
        return f"{self.asset_code}: {self.alias}"

    @property
    def portrait_url(self):
        if self.uploaded_portrait:
            return self.uploaded_portrait.url
        return self.portrait


class AssetObservation(models.Model):
    class Kind(models.TextChoices):
        ROUTINE = "routine", "Routine"
        WARNING = "warning", "Warning"
        DISPUTED = "disputed", "Disputed"
        ADMINISTRATIVE = "admin", "Administrative"

    reference = models.CharField(max_length=24, unique=True)
    asset = models.ForeignKey(
        HumanAsset,
        on_delete=models.CASCADE,
        related_name="observations",
        blank=True,
        null=True,
    )
    observed_on = models.DateField()
    kind = models.CharField(max_length=10, choices=Kind.choices)
    summary = models.TextField()

    class Meta:
        ordering = ("-observed_on", "reference")

    def __str__(self):
        return self.reference


class Directive(models.Model):
    class Priority(models.TextChoices):
        WHENEVER = "whenever", "Whenever"
        ROUTINE = "routine", "Routine"
        IMPORTANT = "important", "Important"
        ABSOLUTE = "absolute", "Absolutely do this"

    code = models.CharField(max_length=20, primary_key=True)
    priority = models.CharField(max_length=10, choices=Priority.choices)
    instruction = models.TextField()
    rationale = models.TextField()
    status_line = models.CharField(max_length=180)
    position = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("position", "code")

    def __str__(self):
        return self.code


class ArchiveDocument(models.Model):
    code = models.CharField(max_length=20, primary_key=True)
    title = models.CharField(max_length=180)
    classification = models.CharField(max_length=80)
    filed_on = models.DateField()
    summary = models.TextField()
    excerpt = models.TextField()
    redaction_level = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(5)],
    )
    is_visible = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("-filed_on", "code")

    def __str__(self):
        return f"{self.code}: {self.title}"
