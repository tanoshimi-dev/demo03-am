from django.contrib.auth.models import User
from django.db import models

from assets.models import Asset


class LoanRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "審査中"),
        (STATUS_APPROVED, "承認済み"),
        (STATUS_REJECTED, "却下"),
        (STATUS_CANCELLED, "キャンセル"),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="loan_requests")
    requester = models.ForeignKey(User, on_delete=models.PROTECT, related_name="loan_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    purpose = models.TextField(blank=True)
    expected_start_date = models.DateField()
    expected_return_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Loan request"
        verbose_name_plural = "Loan requests"

    def __str__(self) -> str:
        return f"{self.requester.username} / {self.asset.asset_code} ({self.get_status_display()})"

    @property
    def is_active(self) -> bool:
        return self.status in (self.STATUS_PENDING, self.STATUS_APPROVED)


class LoanRecord(models.Model):
    loan_request = models.OneToOneField(
        LoanRequest, on_delete=models.PROTECT, related_name="loan_record"
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="approved_loans"
    )
    loan_start_date = models.DateField()
    expected_return_date = models.DateField(null=True, blank=True)
    return_requested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Loan record"
        verbose_name_plural = "Loan records"

    def __str__(self) -> str:
        return f"{self.loan_request.asset.asset_code} → {self.loan_request.requester.username}"

    @property
    def is_on_loan(self) -> bool:
        return not hasattr(self, "return_record")


class ReturnRecord(models.Model):
    loan_record = models.OneToOneField(
        LoanRecord, on_delete=models.PROTECT, related_name="return_record"
    )
    received_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="received_returns"
    )
    returned_at = models.DateTimeField()
    condition_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-returned_at"]
        verbose_name = "Return record"
        verbose_name_plural = "Return records"

    def __str__(self) -> str:
        return f"Return: {self.loan_record.loan_request.asset.asset_code} at {self.returned_at}"
