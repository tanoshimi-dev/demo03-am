from django.contrib import admin

from .models import IncidentReport


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "asset",
        "incident_type",
        "status",
        "reported_by",
        "reported_at",
        "resolved_by",
    )
    list_filter = ("incident_type", "status")
    ordering = ("-reported_at",)
    search_fields = ("asset__asset_code", "asset__name", "description", "reported_by__username")
    autocomplete_fields = ("asset",)
    readonly_fields = ("reported_at", "created_at", "updated_at")
