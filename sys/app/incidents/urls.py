from django.urls import path

from .views import IncidentListView, IncidentReportCreateView, IncidentResolveView

app_name = "incidents"

urlpatterns = [
    path("incidents/", IncidentListView.as_view(), name="list"),
    path("incidents/report/<str:asset_code>/", IncidentReportCreateView.as_view(), name="report"),
    path("incidents/<int:pk>/resolve/", IncidentResolveView.as_view(), name="resolve"),
]
