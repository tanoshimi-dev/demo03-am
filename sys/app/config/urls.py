from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("", include("accounts.urls")),
    path("", include("assets.urls")),
    path("", include("loans.urls")),
    path("", include("incidents.urls")),
    path("", include("inventory.urls")),
    path("", include("auditlogs.urls")),
    path("admin/", admin.site.urls),
]
