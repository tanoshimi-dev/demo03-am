from django.contrib import admin

from .models import Asset, AssetCategory


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active",)
    ordering = ("sort_order", "name")
    search_fields = ("code", "name", "description")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("asset_code", "name", "category", "status", "serial_number", "location", "updated_at")
    list_filter = ("status", "category")
    ordering = ("asset_code",)
    search_fields = ("asset_code", "name", "serial_number", "manufacturer", "model_name", "location")
    autocomplete_fields = ("category",)
