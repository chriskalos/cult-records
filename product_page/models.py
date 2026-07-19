from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models

from home.models import Product


def validate_track_list(value):
    if not isinstance(value, list):
        raise ValidationError("Tracks must be provided as a list.")

    if any(not isinstance(track, str) or not track.strip() for track in value):
        raise ValidationError("Every track must have a name.")


class ProductPage(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="page",
    )
    long_description = models.TextField(blank=True)
    release_date = models.DateField(blank=True, null=True)
    tracks = models.JSONField(
        blank=True,
        default=list,
        validators=[validate_track_list],
    )

    def clean(self):
        super().clean()
        if isinstance(self.tracks, list):
            self.tracks = [track.strip() for track in self.tracks]

    def __str__(self):
        return f"Product page for {self.product}"


class Review(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(
        blank=True,
        max_length=2000,
        validators=[MaxLengthValidator(2000)],
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    rejection_reason = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "author"],
                name="one_review_per_product_author",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_between_1_and_5",
            ),
        ]

    def clean(self):
        super().clean()
        self.comment = self.comment.strip()
        self.rejection_reason = self.rejection_reason.strip()
        if self.status != self.Status.REJECTED:
            self.rejection_reason = ""

    def save(self, *args, **kwargs):
        self.comment = self.comment.strip()
        self.rejection_reason = self.rejection_reason.strip()
        if self.status != self.Status.REJECTED:
            self.rejection_reason = ""
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rating}/5 review of {self.product} by {self.author}"
