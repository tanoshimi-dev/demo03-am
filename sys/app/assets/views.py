from django.db import models
from django.views.generic import DetailView, ListView

from accounts.mixins import PortalLoginRequiredMixin

from .models import Asset, AssetCategory


def can_manage_assets(request) -> bool:
    account = getattr(request, "account", None)
    if account is None:
        return False
    role_codes = set(account.roles.values_list("code", flat=True))
    return bool(role_codes.intersection({"asset-admin", "sysadmin"}))


class AssetListView(PortalLoginRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            Asset.objects.select_related("category")
            .order_by("asset_code")
        )

        search_query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        category_code = self.request.GET.get("category", "").strip()

        if search_query:
            queryset = queryset.filter(
                models.Q(asset_code__icontains=search_query)
                | models.Q(name__icontains=search_query)
                | models.Q(serial_number__icontains=search_query)
                | models.Q(manufacturer__icontains=search_query)
                | models.Q(model_name__icontains=search_query)
                | models.Q(location__icontains=search_query)
                | models.Q(category__name__icontains=search_query)
            )

        if status:
            queryset = queryset.filter(status=status)

        if category_code:
            queryset = queryset.filter(category__code=category_code)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["selected_status"] = self.request.GET.get("status", "").strip()
        context["selected_category"] = self.request.GET.get("category", "").strip()
        context["status_choices"] = Asset.STATUS_CHOICES
        context["categories"] = AssetCategory.objects.filter(is_active=True).order_by("sort_order", "name")
        context["can_manage_assets"] = can_manage_assets(self.request)
        return context


class AssetDetailView(PortalLoginRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"
    slug_field = "asset_code"
    slug_url_kwarg = "asset_code"

    def get_queryset(self):
        return Asset.objects.select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_assets"] = can_manage_assets(self.request)
        return context
