from django.urls import path

from .views import (
    InventoryResultInputView,
    InventorySessionCloseView,
    InventorySessionCreateView,
    InventorySessionDetailView,
    InventorySessionListView,
)

app_name = "inventory"

urlpatterns = [
    path("inventory/", InventorySessionListView.as_view(), name="session_list"),
    path("inventory/new/", InventorySessionCreateView.as_view(), name="session_create"),
    path("inventory/<int:pk>/", InventorySessionDetailView.as_view(), name="session_detail"),
    path("inventory/<int:pk>/close/", InventorySessionCloseView.as_view(), name="session_close"),
    path(
        "inventory/<int:session_pk>/record/<str:asset_code>/",
        InventoryResultInputView.as_view(),
        name="result_input",
    ),
]
