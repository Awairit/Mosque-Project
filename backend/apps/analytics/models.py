import uuid
from django.db import models
from apps.common.models import TimeStampedModel


class AnonymousVisitor(TimeStampedModel):
    """
    Privacy-conscious anonymous visitor session token.
    Contains zero PII (no IP address, no fingerprinting, no phone, no email).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_seen = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen = models.DateTimeField(auto_now=True, db_index=True)
    visit_count = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-last_seen"]
        indexes = [
            models.Index(fields=["first_seen", "last_seen"]),
        ]

    def __str__(self) -> str:
        return f"Visitor {str(self.id)[:8]} ({self.visit_count} visits)"


class VisitEvent(TimeStampedModel):
    """
    Lightweight page/section view event for product adoption tracking.
    """

    visitor = models.ForeignKey(
        AnonymousVisitor,
        on_delete=models.CASCADE,
        related_name="visits",
        db_index=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    path = models.CharField(max_length=255, db_index=True)
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visit_events",
    )
    mosque = models.ForeignKey(
        "mosques.Mosque",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visit_events",
    )
    event_type = models.CharField(max_length=50, default="page_view", db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp", "city"]),
            models.Index(fields=["visitor", "timestamp"]),
            models.Index(fields=["event_type", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} on {self.path} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
