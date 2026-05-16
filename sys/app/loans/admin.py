from django.contrib import admin

from .models import LoanRecord, LoanRequest, ReturnRecord


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = (
        "pk", "asset", "requester", "status",
        "expected_start_date", "expected_return_date", "created_at",
    )
    list_filter = ("status",)
    ordering = ("-created_at",)
    search_fields = ("asset__asset_code", "asset__name", "requester__username")
    autocomplete_fields = ("asset",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(LoanRecord)
class LoanRecordAdmin(admin.ModelAdmin):
    list_display = (
        "pk", "loan_request", "approved_by",
        "loan_start_date", "expected_return_date", "created_at",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ReturnRecord)
class ReturnRecordAdmin(admin.ModelAdmin):
    list_display = ("pk", "loan_record", "received_by", "returned_at", "created_at")
    ordering = ("-returned_at",)
    readonly_fields = ("created_at", "updated_at")
