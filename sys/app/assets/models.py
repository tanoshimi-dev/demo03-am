from django.db import models


class AssetCategory(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name", "code"]
        verbose_name = "Asset category"
        verbose_name_plural = "Asset categories"

    def __str__(self) -> str:
        return self.name


class Asset(models.Model):
    STATUS_IN_STOCK = "in_stock"
    STATUS_ON_LOAN = "on_loan"
    STATUS_IN_REPAIR = "in_repair"
    STATUS_LOST = "lost"
    STATUS_RETIRED = "retired"
    STATUS_CHOICES = [
        (STATUS_IN_STOCK, "In stock"),
        (STATUS_ON_LOAN, "On loan"),
        (STATUS_IN_REPAIR, "In repair"),
        (STATUS_LOST, "Lost"),
        (STATUS_RETIRED, "Retired"),
    ]

    asset_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name="assets")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_STOCK)
    serial_number = models.CharField(max_length=100, unique=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    acquired_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset_code"]
        verbose_name = "Asset"
        verbose_name_plural = "Assets"

    def __str__(self) -> str:
        return f"{self.asset_code} {self.name}"

    @property
    def is_available_for_loan(self) -> bool:
        return self.status == self.STATUS_IN_STOCK
