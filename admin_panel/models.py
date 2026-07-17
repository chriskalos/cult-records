from django.conf import settings
from django.db import models


class AdminActivity(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Created"
        UPDATE = "update", "Updated"
        DELETE = "delete", "Deleted"
        PASSWORD = "password", "Changed password"
        ROLE = "role", "Changed role"
        VISIBILITY = "visibility", "Changed visibility"
        MODERATION = "moderation", "Moderated"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="admin_activities",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    target_type = models.CharField(max_length=80)
    target_identifier = models.CharField(max_length=255)
    target_label = models.CharField(max_length=255)
    summary = models.TextField()
    metadata = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        actor = self.actor.username if self.actor else "Deleted administrator"
        return f"{actor} {self.get_action_display().lower()} {self.target_label}"
