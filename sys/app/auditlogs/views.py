from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView

from .models import AuditLog


def can_manage_auditlogs(request) -> bool:
    account = getattr(request, "account", None)
    if account is None:
        return False
    role_codes = set(account.roles.values_list("code", flat=True))
    return bool(role_codes.intersection({"asset-admin", "sysadmin"}))


class AdminAuditRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            query = urlencode({"returnTo": request.get_full_path()})
            return redirect(f"{reverse('accounts:handover')}?{query}")
        if not can_manage_auditlogs(request):
            return redirect("assets:list")
        return super().dispatch(request, *args, **kwargs)


class AuditLogListView(AdminAuditRequiredMixin, ListView):
    model = AuditLog
    template_name = "auditlogs/auditlog_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("actor")
        action = self.request.GET.get("action", "").strip()
        asset_code = self.request.GET.get("asset_code", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        if asset_code:
            queryset = queryset.filter(asset_code__icontains=asset_code)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_action"] = self.request.GET.get("action", "").strip()
        context["asset_code_query"] = self.request.GET.get("asset_code", "").strip()
        context["action_choices"] = AuditLog.ACTION_CHOICES
        return context
