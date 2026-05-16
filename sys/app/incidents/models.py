from django.contrib.auth.models import User
from django.db import models

from assets.models import Asset


class IncidentReport(models.Model):
    TYPE_BREAKDOWN = "breakdown"
    TYPE_LOST = "lost"
    TYPE_RETIRED = "retired"
    TYPE_CHOICES = [
        (TYPE_BREAKDOWN, "故障"),
        (TYPE_LOST, "紛失"),
        (TYPE_RETIRED, "廃棄"),
    ]

    STATUS_OPEN = "open"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = [
        (STATUS_OPEN, "対応中"),
        (STATUS_RESOLVED, "解決済み"),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="incident_reports")
    incident_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="reported_incidents"
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_incidents",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-reported_at"]
        verbose_name = "Incident report"
        verbose_name_plural = "Incident reports"

    def __str__(self) -> str:
        return (
            f"{self.get_incident_type_display()} / {self.asset.asset_code} "
            f"({self.get_status_display()})"
        )
