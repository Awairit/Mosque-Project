"""Models for platform admin workflows and audit logging."""

from django.db import models
from django.contrib.auth.models import User
from apps.common.models import TimeStampedModel
from apps.mosques.models import Mosque


class MosqueApprovalLog(TimeStampedModel):
    """Audit log tracking approvals and rejections of mosque registrations."""

    class ActionTypes(models.TextChoices):
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"

    action = models.CharField(
        max_length=20,
        choices=ActionTypes.choices,
    )
    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_logs",
    )
    registration_request_id = models.IntegerField(null=True, blank=True)
    mosque_name = models.CharField(max_length=255)
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="platform_approval_logs",
    )
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "platform_admin_mosqueapprovallog"

    def __str__(self) -> str:
        return f"{self.action.upper()} - {self.mosque_name} by {self.admin.username}"
