from django.urls import path

from .views import AuditLogListView

app_name = "auditlogs"

urlpatterns = [
    path("auditlogs/", AuditLogListView.as_view(), name="list"),
]
