from django.urls import path

from .views import LoanRequestAdminListView, LoanRequestCreateView, MyLoanListView

app_name = "loans"

urlpatterns = [
    path("loans/request/<str:asset_code>/", LoanRequestCreateView.as_view(), name="request"),
    path("loans/mine/", MyLoanListView.as_view(), name="my_list"),
    path("loans/admin/", LoanRequestAdminListView.as_view(), name="admin_list"),
]
