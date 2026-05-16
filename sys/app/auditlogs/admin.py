from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("pk", "action", "actor", "asset_code", "object_repr", "created_at")
    list_filter = ("action",)
    ordering = ("-created_at",)
    search_fields = ("asset_code", "object_repr", "actor__username")
    readonly_fields = ("action", "actor", "asset_code", "object_repr", "extra", "created_at")
