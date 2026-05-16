from django.contrib.auth.models import User
from django.db import models

from assets.models import Asset


class InventorySession(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "実施中"),
        (STATUS_CLOSED, "完了"),
    ]

    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="created_inventory_sessions"
    )
    closed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="closed_inventory_sessions",
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_status_display()})"


class InventoryResult(models.Model):
    STATUS_CONFIRMED = "confirmed"
    STATUS_MISSING = "missing"
    STATUS_CHOICES = [
        (STATUS_CONFIRMED, "確認済み"),
        (STATUS_MISSING, "所在不明"),
    ]

    session = models.ForeignKey(
        InventorySession, on_delete=models.CASCADE, related_name="results"
    )
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="inventory_results")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="recorded_inventory_results"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("session", "asset")]

    def __str__(self) -> str:
        return f"{self.session.name} / {self.asset.asset_code} ({self.get_status_display()})"
