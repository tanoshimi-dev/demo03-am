from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, ListView, View

from assets.models import Asset

from .forms import IncidentReportForm, IncidentResolveForm
from .models import IncidentReport
from .services import IncidentError, report_incident, resolve_incident


def can_manage_incidents(request) -> bool:
    account = getattr(request, "account", None)
    if account is None:
        return False
    role_codes = set(account.roles.values_list("code", flat=True))
    return bool(role_codes.intersection({"asset-admin", "sysadmin"}))


class AdminIncidentRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            query = urlencode({"returnTo": request.get_full_path()})
            return redirect(f"{reverse('accounts:handover')}?{query}")
        if not can_manage_incidents(request):
            return redirect("assets:list")
        return super().dispatch(request, *args, **kwargs)


class IncidentListView(AdminIncidentRequiredMixin, ListView):
    model = IncidentReport
    template_name = "incidents/incident_list.html"
    context_object_name = "incident_reports"
    paginate_by = 50

    def get_queryset(self):
        queryset = IncidentReport.objects.select_related(
            "asset", "asset__category", "reported_by", "resolved_by"
        )
        selected_status = self.request.GET.get("status", "").strip()
        selected_type = self.request.GET.get("incident_type", "").strip()
        if selected_status:
            queryset = queryset.filter(status=selected_status)
        if selected_type:
            queryset = queryset.filter(incident_type=selected_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "").strip()
        context["selected_type"] = self.request.GET.get("incident_type", "").strip()
        context["status_choices"] = IncidentReport.STATUS_CHOICES
        context["type_choices"] = IncidentReport.TYPE_CHOICES
        return context


class IncidentReportCreateView(AdminIncidentRequiredMixin, CreateView):
    model = IncidentReport
    form_class = IncidentReportForm
    template_name = "incidents/incident_report_form.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.asset = get_object_or_404(Asset.objects.select_related("category"), asset_code=kwargs["asset_code"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asset"] = self.asset
        return context

    def form_valid(self, form):
        try:
            report_incident(
                asset=self.asset,
                incident_type=form.cleaned_data["incident_type"],
                reporter=self.request.user,
                description=form.cleaned_data.get("description", ""),
            )
        except IncidentError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "インシデントを記録しました。")
        return redirect("incidents:list")


class IncidentResolveView(AdminIncidentRequiredMixin, View):
    def get_incident(self, pk: int) -> IncidentReport:
        return get_object_or_404(
            IncidentReport.objects.select_related("asset", "asset__category", "reported_by"),
            pk=pk,
        )

    def _ensure_resolvable(self, request, incident_report: IncidentReport):
        if incident_report.incident_type != IncidentReport.TYPE_BREAKDOWN:
            messages.error(request, "故障インシデントのみ解決できます。")
            return redirect("incidents:list")
        if incident_report.status == IncidentReport.STATUS_RESOLVED:
            messages.error(request, "このインシデントはすでに解決済みです。")
            return redirect("incidents:list")
        return None

    def get(self, request, pk):
        incident_report = self.get_incident(pk)
        redirect_response = self._ensure_resolvable(request, incident_report)
        if redirect_response is not None:
            return redirect_response
        form = IncidentResolveForm()
        return render(
            request,
            "incidents/incident_resolve_form.html",
            {"incident_report": incident_report, "form": form},
        )

    def post(self, request, pk):
        incident_report = self.get_incident(pk)
        redirect_response = self._ensure_resolvable(request, incident_report)
        if redirect_response is not None:
            return redirect_response
        form = IncidentResolveForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "incidents/incident_resolve_form.html",
                {"incident_report": incident_report, "form": form},
                status=200,
            )
        try:
            resolve_incident(
                incident_report=incident_report,
                resolver=request.user,
                resolution_notes=form.cleaned_data["resolution_notes"],
            )
        except IncidentError as exc:
            form.add_error(None, str(exc))
            return render(
                request,
                "incidents/incident_resolve_form.html",
                {"incident_report": incident_report, "form": form},
                status=200,
            )
        messages.success(request, "故障インシデントを解決し、資産を在庫に戻しました。")
        return redirect("incidents:list")
