from django.contrib import admin

from .models import Account, AccountSession, AppRole


@admin.register(AppRole)
class AppRoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "updated_at")
    search_fields = ("code", "name")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "portal_subject", "is_portal_active", "last_handover_at")
    list_filter = ("is_portal_active", "roles")
    search_fields = ("display_name", "email", "portal_subject", "user__username")
    filter_horizontal = ("roles",)


@admin.register(AccountSession)
class AccountSessionAdmin(admin.ModelAdmin):
    list_display = ("account", "source", "session_key", "last_seen_at", "ended_at")
    list_filter = ("source", "ended_at")
    search_fields = ("account__display_name", "account__email", "session_key")
