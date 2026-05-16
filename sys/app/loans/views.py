from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, ListView

from accounts.mixins import PortalLoginRequiredMixin
from assets.models import Asset

from .forms import LoanRequestForm
from .models import LoanRequest
from .services import LoanEligibilityError, create_loan_request


def can_manage_loans(request) -> bool:
    account = getattr(request, "account", None)
    if account is None:
        return False
    role_codes = set(account.roles.values_list("code", flat=True))
    return bool(role_codes.intersection({"asset-admin", "sysadmin"}))


class LoanRequestCreateView(PortalLoginRequiredMixin, CreateView):
    model = LoanRequest
    form_class = LoanRequestForm
    template_name = "loans/loan_request_form.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.asset = get_object_or_404(Asset, asset_code=kwargs["asset_code"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asset"] = self.asset
        return context

    def form_valid(self, form):
        try:
            loan_request = create_loan_request(
                asset=self.asset,
                requester=self.request.user,
                **form.cleaned_data,
            )
        except LoanEligibilityError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"貸出申請を受け付けました（申請番号: {loan_request.pk}）。",
        )
        return redirect("loans:my_list")


class MyLoanListView(PortalLoginRequiredMixin, ListView):
    model = LoanRequest
    template_name = "loans/my_loan_list.html"
    context_object_name = "loan_requests"

    def get_queryset(self):
        return (
            LoanRequest.objects.select_related("asset", "asset__category")
            .filter(requester=self.request.user)
            .order_by("-created_at")
        )


class LoanRequestAdminListView(PortalLoginRequiredMixin, ListView):
    model = LoanRequest
    template_name = "loans/loan_request_admin_list.html"
    context_object_name = "loan_requests"
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from urllib.parse import urlencode

            from django.urls import reverse

            query = urlencode({"returnTo": request.get_full_path()})
            return redirect(f"{reverse('accounts:handover')}?{query}")
        if not can_manage_loans(request):
            return redirect("loans:my_list")
        return super(PortalLoginRequiredMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = LoanRequest.objects.select_related(
            "asset", "asset__category", "requester"
        ).order_by("-created_at")
        status = self.request.GET.get("status", "").strip()
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "").strip()
        context["status_choices"] = LoanRequest.STATUS_CHOICES
        return context
