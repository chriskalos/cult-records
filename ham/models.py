from django.conf import settings
from django.db import models


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
