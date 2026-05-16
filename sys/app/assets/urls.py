from django.urls import path

from .views import AssetDetailView, AssetListView

app_name = "assets"

urlpatterns = [
    path("assets/", AssetListView.as_view(), name="list"),
    path("assets/<str:asset_code>/", AssetDetailView.as_view(), name="detail"),
]
