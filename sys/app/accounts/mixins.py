from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


class PortalLoginRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            query = urlencode({"returnTo": request.get_full_path()})
            return redirect(f"{reverse('accounts:handover')}?{query}")
        return super().dispatch(request, *args, **kwargs)
