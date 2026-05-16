from django.urls import path

from .views import (
    LoanApproveView,
    LoanRejectView,
    LoanRequestAdminListView,
    LoanRequestCreateView,
    MyLoanListView,
    ReturnConfirmView,
    ReturnRequestView,
)

app_name = "loans"

urlpatterns = [
    path("loans/request/<str:asset_code>/", LoanRequestCreateView.as_view(), name="request"),
    path("loans/mine/", MyLoanListView.as_view(), name="my_list"),
    path("loans/admin/", LoanRequestAdminListView.as_view(), name="admin_list"),
    path("loans/admin/<int:pk>/approve/", LoanApproveView.as_view(), name="approve"),
    path("loans/admin/<int:pk>/reject/", LoanRejectView.as_view(), name="reject"),
    path("loans/mine/<int:pk>/return-request/", ReturnRequestView.as_view(), name="return_request"),
    path("loans/admin/return-confirm/<int:pk>/", ReturnConfirmView.as_view(), name="return_confirm"),
]
