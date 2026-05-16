from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, ListView, View

from accounts.mixins import PortalLoginRequiredMixin
from assets.models import Asset

from .forms import LoanRequestForm
from .models import LoanRecord, LoanRequest, ReturnRecord
from .services import (
    LoanEligibilityError,
    LoanTransitionError,
    approve_loan_request,
    confirm_return,
    create_loan_request,
    reject_loan_request,
    request_return,
)


def can_manage_loans(request) -> bool:
    account = getattr(request, "account", None)
    if account is None:
        return False
    role_codes = set(account.roles.values_list("code", flat=True))
    return bool(role_codes.intersection({"asset-admin", "sysadmin"}))


class AdminLoanRequiredMixin:
    """Requires authenticated user with loan management role."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            query = urlencode({"returnTo": request.get_full_path()})
            return redirect(f"{reverse('accounts:handover')}?{query}")
        if not can_manage_loans(request):
            return redirect("loans:my_list")
        return super().dispatch(request, *args, **kwargs)


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
            .prefetch_related("loan_record")
            .filter(requester=self.request.user)
            .order_by("-created_at")
        )


class LoanRequestAdminListView(AdminLoanRequiredMixin, ListView):
    model = LoanRequest
    template_name = "loans/loan_request_admin_list.html"
    context_object_name = "loan_requests"
    paginate_by = 50

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
        context["active_loans"] = LoanRecord.objects.select_related(
            "loan_request__asset",
            "loan_request__asset__category",
            "loan_request__requester",
        ).filter(return_record__isnull=True).order_by("-created_at")
        return context


class LoanApproveView(AdminLoanRequiredMixin, View):
    def post(self, request, pk):
        loan_request = get_object_or_404(LoanRequest, pk=pk)
        try:
            approve_loan_request(loan_request=loan_request, approver=request.user)
            messages.success(request, f"申請番号 {pk} を承認しました。")
        except LoanTransitionError as exc:
            messages.error(request, str(exc))
        return redirect("loans:admin_list")


class LoanRejectView(AdminLoanRequiredMixin, View):
    def post(self, request, pk):
        loan_request = get_object_or_404(LoanRequest, pk=pk)
        try:
            reject_loan_request(loan_request=loan_request, rejector=request.user)
            messages.success(request, f"申請番号 {pk} を却下しました。")
        except LoanTransitionError as exc:
            messages.error(request, str(exc))
        return redirect("loans:admin_list")


class ReturnRequestView(PortalLoginRequiredMixin, View):
    def post(self, request, pk):
        loan_record = get_object_or_404(
            LoanRecord, pk=pk, loan_request__requester=request.user
        )
        try:
            request_return(loan_record=loan_record)
            messages.success(request, "返却申請を提出しました。")
        except LoanTransitionError as exc:
            messages.error(request, str(exc))
        return redirect("loans:my_list")


class ReturnConfirmView(AdminLoanRequiredMixin, View):
    def get(self, request, pk):
        loan_record = get_object_or_404(LoanRecord, pk=pk)
        return render(request, "loans/return_confirm_form.html", {"loan_record": loan_record})

    def post(self, request, pk):
        loan_record = get_object_or_404(LoanRecord, pk=pk)
        condition_notes = request.POST.get("condition_notes", "")
        try:
            confirm_return(
                loan_record=loan_record,
                receiver=request.user,
                condition_notes=condition_notes,
            )
            messages.success(request, "返却を確認しました。資産を在庫に戻しました。")
        except LoanTransitionError as exc:
            messages.error(request, str(exc))
        return redirect("loans:admin_list")
