from django.contrib.auth.models import User
from django.db import models


class AuditLog(models.Model):
    ACTION_LOAN_REQUESTED = "loan_requested"
    ACTION_LOAN_APPROVED = "loan_approved"
    ACTION_LOAN_REJECTED = "loan_rejected"
    ACTION_RETURN_REQUESTED = "return_requested"
    ACTION_RETURN_CONFIRMED = "return_confirmed"
    ACTION_INCIDENT_REPORTED = "incident_reported"
    ACTION_INCIDENT_RESOLVED = "incident_resolved"
    ACTION_INVENTORY_RECORDED = "inventory_recorded"
    ACTION_INVENTORY_CLOSED = "inventory_closed"
    ACTION_CHOICES = [
        (ACTION_LOAN_REQUESTED, "貸出申請"),
        (ACTION_LOAN_APPROVED, "貸出承認"),
        (ACTION_LOAN_REJECTED, "貸出却下"),
        (ACTION_RETURN_REQUESTED, "返却申請"),
        (ACTION_RETURN_CONFIRMED, "返却確認"),
        (ACTION_INCIDENT_REPORTED, "インシデント報告"),
        (ACTION_INCIDENT_RESOLVED, "インシデント解決"),
        (ACTION_INVENTORY_RECORDED, "棚卸し結果記録"),
        (ACTION_INVENTORY_CLOSED, "棚卸し完了"),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    asset_code = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit log"
        verbose_name_plural = "Audit logs"

    def __str__(self) -> str:
        target = self.asset_code or self.object_repr or "-"
        return f"{self.get_action_display()} / {target} ({self.created_at:%Y-%m-%d %H:%M})"
