from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("auth/me", views.me_view, name="me"),
    path("auth/handover", views.handover_view, name="handover"),
    path("auth/demo-switch", views.demo_switch_view, name="demo_switch"),
    path("auth/logout", views.logout_view, name="logout"),
]
