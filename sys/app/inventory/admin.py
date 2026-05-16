from django.contrib import admin

from .models import InventoryResult, InventorySession


@admin.register(InventorySession)
class InventorySessionAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "status", "created_by", "created_at", "closed_by", "closed_at")
    list_filter = ("status",)
    ordering = ("-created_at",)
    search_fields = ("name", "notes", "created_by__username")
    readonly_fields = ("created_at", "updated_at", "closed_at")


@admin.register(InventoryResult)
class InventoryResultAdmin(admin.ModelAdmin):
    list_display = ("pk", "session", "asset", "status", "recorded_by", "created_at")
    list_filter = ("status", "session")
    ordering = ("-created_at",)
    search_fields = ("session__name", "asset__asset_code", "asset__name", "notes")
    autocomplete_fields = ("session", "asset")
    readonly_fields = ("created_at", "updated_at")
