from django.conf import settings
from django.contrib.auth import login, logout
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Account, AccountSession
from .services import (
    _get_jwks_client,
    _jwt,
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


@require_POST
def demo_switch_view(request):
    if settings.AUTH_MODE != "dev-header":
        return HttpResponseForbidden("Demo switch is only available in dev-header mode.")

    portal_subject = request.POST.get("portal_subject", "").strip()
    allowed = getattr(settings, "DEMO_SWITCH_SUBJECTS", [])
    if portal_subject not in allowed:
        return HttpResponseBadRequest("Invalid portal_subject.")

    try:
        account = Account.objects.select_related("user").get(portal_subject=portal_subject)
    except Account.DoesNotExist:
        return HttpResponseBadRequest(
            f"Account not found for portal_subject={portal_subject!r}. "
            "Run 'python manage.py load_demo_seed' first."
        )

    return_to = sanitize_return_to(request, request.POST.get("returnTo"), _default_return_to())
    previous_session_key = request.session.session_key
    logout(request)
    end_account_session(previous_session_key)
    login(request, account.user, backend="django.contrib.auth.backends.ModelBackend")
    sync_account_session(request, account, AccountSession.SOURCE_DEV_HEADER)
    request.account = account
    return redirect(return_to)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    return_to = sanitize_return_to(request, request.GET.get("returnTo"), _default_return_to())
    end_account_session(request.session.session_key)
    logout(request)
    return redirect(return_to)


@require_GET
def jwt_check_view(request):
    if not (settings.DEBUG or (request.user.is_authenticated and request.user.is_staff)):
        return HttpResponseForbidden("This page is only available in DEBUG mode or to staff users.")

    import datetime

    cookie_names = list(settings.PORTAL_COOKIE_NAMES)
    jwks_url = (getattr(settings, "PORTAL_JWKS_URL", "") or "").strip()
    issuer = (getattr(settings, "PORTAL_ISSUER", "") or "").strip()
    auth_mode = settings.AUTH_MODE

    # Find the first present cookie
    raw_token: str | None = None
    found_cookie_name: str | None = None
    cookie_status: list[dict] = []
    for name in cookie_names:
        value = request.COOKIES.get(name, "").strip()
        present = bool(value)
        if present and raw_token is None:
            raw_token = value
            found_cookie_name = name
        masked = (value[:12] + "..." + value[-6:]) if len(value) > 20 else (value or "—")
        cookie_status.append({"name": name, "present": present, "masked": masked if present else "—"})

    # Decode without verification to inspect claims
    unverified_header: dict | None = None
    unverified_claims: dict | None = None
    unverified_error: str | None = None
    if raw_token:
        try:
            unverified_header = _jwt.get_unverified_header(raw_token)
            unverified_claims = _jwt.decode(
                raw_token,
                options={"verify_signature": False},
                algorithms=["RS256"],
            )
        except Exception as exc:
            unverified_error = str(exc)

    # Check expiry from unverified claims
    exp_info: dict | None = None
    if unverified_claims and "exp" in unverified_claims:
        exp_ts = unverified_claims["exp"]
        try:
            exp_dt = datetime.datetime.fromtimestamp(exp_ts, tz=datetime.timezone.utc)
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            exp_info = {
                "timestamp": exp_ts,
                "datetime": exp_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "expired": now > exp_dt,
                "remaining_seconds": max(0, int((exp_dt - now).total_seconds())),
            }
        except Exception:
            exp_info = {"timestamp": exp_ts, "datetime": "—", "expired": None, "remaining_seconds": 0}

    # Signature verification
    verify_result: dict = {"status": "skipped", "error": None}
    if raw_token and jwks_url:
        try:
            client = _get_jwks_client(jwks_url)
            signing_key = client.get_signing_key_from_jwt(raw_token)
            _jwt.decode(
                raw_token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=issuer or None,
                options={"require": ["sub", "email", "exp"]},
            )
            verify_result = {"status": "pass", "error": None}
        except Exception as exc:
            verify_result = {"status": "fail", "error": str(exc)}
    elif raw_token and not jwks_url:
        verify_result = {"status": "skipped", "error": "PORTAL_JWKS_URL is not configured"}

    context = {
        "auth_mode": auth_mode,
        "jwks_url": jwks_url or "—",
        "issuer": issuer or "—",
        "cookie_names": cookie_names,
        "cookie_status": cookie_status,
        "found_cookie_name": found_cookie_name,
        "unverified_header": unverified_header,
        "unverified_claims": unverified_claims,
        "unverified_error": unverified_error,
        "exp_info": exp_info,
        "verify_result": verify_result,
    }
    return render(request, "accounts/jwt_check.html", context)
