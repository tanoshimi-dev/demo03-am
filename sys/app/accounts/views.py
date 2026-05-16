from django.conf import settings
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .models import Account
from .services import (
    account_payload,
    build_portal_login_url,
    end_account_session,
    establish_account_session,
    resolve_portal_identity,
    sanitize_return_to,
    sync_account_session,
)


def _default_return_to() -> str:
    return reverse("home")


@require_GET
def me_view(request):
    handover_url = f"{reverse('accounts:handover')}?returnTo={_default_return_to()}"
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": False,
                "authMode": settings.AUTH_MODE,
                "handoverUrl": handover_url,
            },
            status=401,
        )

    account = getattr(request, "account", None)
    if isinstance(account, Account):
        payload = account_payload(account)
    else:
        payload = {
            "displayName": request.user.get_full_name() or request.user.get_username(),
            "email": request.user.email,
            "portalSubject": "",
            "roles": [],
        }

    return JsonResponse(
        {
            "authenticated": True,
            "authMode": settings.AUTH_MODE,
            "user": payload,
            "logoutUrl": f"{reverse('accounts:logout')}?returnTo={_default_return_to()}",
        }
    )


@require_GET
def handover_view(request):
    return_to = sanitize_return_to(request, request.GET.get("returnTo"), _default_return_to())
    identity = resolve_portal_identity(request)
    if identity is None:
        portal_login_url = build_portal_login_url(request, return_to)
        if portal_login_url:
            return redirect(portal_login_url)

        return JsonResponse(
            {
                "authenticated": False,
                "detail": "Trusted portal identity was not provided.",
                "authMode": settings.AUTH_MODE,
                "requiredHeaders": [
                    "X-Portal-Subject or X-Portal-User-Sub",
                    "X-Portal-Email or X-Portal-User-Email",
                    "X-Portal-Name or X-Portal-User-Name",
                ],
                "returnTo": return_to,
            },
            status=401,
        )

    previous_session_key = request.session.session_key
    account = establish_account_session(identity)
    login(request, account.user, backend="django.contrib.auth.backends.ModelBackend")
    end_account_session(previous_session_key)
    sync_account_session(request, account, identity.source)
    request.account = account
    return redirect(return_to)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    return_to = sanitize_return_to(request, request.GET.get("returnTo"), _default_return_to())
    end_account_session(request.session.session_key)
    logout(request)
    return redirect(return_to)
