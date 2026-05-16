from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, View

from assets.models import Asset

from .forms import InventoryResultForm, InventorySessionForm
from .models import InventoryResult, InventorySession
from .services import (
    InventoryError,
    close_inventory_session,
    get_discrepancies,
    open_inventory_session,
    record_inventory_result,
)


def can_manage_inventory(request) -> bool:
    account = getattr(request, "account", None)
    if account is None:
        return False
    role_codes = set(account.roles.values_list("code", flat=True))
    return bool(role_codes.intersection({"asset-admin", "sysadmin"}))


class AdminInventoryRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            query = urlencode({"returnTo": request.get_full_path()})
            return redirect(f"{reverse('accounts:handover')}?{query}")
        if not can_manage_inventory(request):
            return redirect("assets:list")
        return super().dispatch(request, *args, **kwargs)


class InventorySessionListView(AdminInventoryRequiredMixin, ListView):
    model = InventorySession
    template_name = "inventory/session_list.html"
    context_object_name = "sessions"

    def get_queryset(self):
        return InventorySession.objects.select_related("created_by", "closed_by")


class InventorySessionCreateView(AdminInventoryRequiredMixin, CreateView):
    model = InventorySession
    form_class = InventorySessionForm
    template_name = "inventory/session_create_form.html"

    def form_valid(self, form):
        session = open_inventory_session(
            name=form.cleaned_data["name"],
            created_by=self.request.user,
            notes=form.cleaned_data.get("notes", ""),
        )
        messages.success(self.request, "棚卸しセッションを開始しました。")
        return redirect("inventory:session_detail", pk=session.pk)


class InventorySessionDetailView(AdminInventoryRequiredMixin, DetailView):
    model = InventorySession
    template_name = "inventory/session_detail.html"
    context_object_name = "session"

    def get_queryset(self):
        return InventorySession.objects.select_related("created_by", "closed_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        results = list(
            self.object.results.select_related("asset", "asset__category", "recorded_by")
            .order_by("asset__asset_code")
        )
        result_map = {result.asset_id: result for result in results}
        record_rows = []
        for asset in Asset.objects.select_related("category").order_by("asset_code"):
            record_rows.append({"asset": asset, "result": result_map.get(asset.id)})
        context["results"] = results
        context["discrepancies"] = get_discrepancies(self.object)
        context["record_rows"] = record_rows
        context["result_status_choices"] = InventoryResult.STATUS_CHOICES
        return context


class InventoryResultInputView(AdminInventoryRequiredMixin, View):
    def post(self, request, session_pk, asset_code):
        session = get_object_or_404(InventorySession, pk=session_pk)
        asset = get_object_or_404(Asset, asset_code=asset_code)
        form = InventoryResultForm(request.POST)
        if not form.is_valid():
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
            return redirect("inventory:session_detail", pk=session.pk)
        try:
            record_inventory_result(
                session=session,
                asset=asset,
                status=form.cleaned_data["status"],
                recorded_by=request.user,
                notes=form.cleaned_data.get("notes", ""),
            )
            messages.success(request, f"{asset.asset_code} の実査結果を記録しました。")
        except InventoryError as exc:
            messages.error(request, str(exc))
        return redirect("inventory:session_detail", pk=session.pk)


class InventorySessionCloseView(AdminInventoryRequiredMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(InventorySession, pk=pk)
        try:
            close_inventory_session(session=session, closed_by=request.user)
            messages.success(request, "棚卸しセッションを完了しました。")
        except InventoryError as exc:
            messages.error(request, str(exc))
        return redirect("inventory:session_detail", pk=session.pk)
