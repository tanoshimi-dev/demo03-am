from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .models import Account, AccountSession, AppRole


@dataclass(frozen=True)
class PortalIdentity:
    subject: str
    email: str
    display_name: str
    roles: list[str]
    source: str


def sanitize_return_to(request, raw_return_to: str | None, default_path: str = "/") -> str:
    if not raw_return_to:
        return default_path

    parsed = urlparse(raw_return_to)
    if not parsed.scheme and not parsed.netloc:
        return raw_return_to if raw_return_to.startswith("/") else default_path

    if parsed.scheme not in {"http", "https"}:
        return default_path

    allowed_hosts = set(settings.PORTAL_ALLOWED_RETURN_TO_HOSTS)
    allowed_hosts.add(request.get_host())
    if parsed.netloc not in allowed_hosts:
        return default_path

    return raw_return_to


def build_portal_login_url(request, return_to: str) -> str | None:
    if not settings.PORTAL_LOGIN_URL:
        return None

    target = return_to if return_to.startswith("http") else request.build_absolute_uri(return_to)
    query = urlencode({"returnTo": target})
    separator = "&" if "?" in settings.PORTAL_LOGIN_URL else "?"
    return f"{settings.PORTAL_LOGIN_URL}{separator}{query}"


def resolve_portal_identity(request) -> PortalIdentity | None:
    subject = _get_header(request, "X-Portal-Subject", "X-Portal-User-Sub")
    email = _get_header(request, "X-Portal-Email", "X-Portal-User-Email")
    display_name = _get_header(request, "X-Portal-Name", "X-Portal-User-Name")
    roles_text = _get_header(request, "X-Portal-Roles", "X-Portal-User-Roles") or ""

    if not subject or not email:
        return None

    mode = settings.AUTH_MODE
    if mode not in {"dev-header", "portal"}:
        return None

    if mode == "portal":
        verified = (_get_header(request, "X-Portal-Verified") or "").strip().lower()
        if verified not in {"1", "true", "yes", "on"}:
            return None
        source = AccountSession.SOURCE_PORTAL_HEADER
    else:
        source = AccountSession.SOURCE_DEV_HEADER

    roles = [normalize_role_code(role) for role in roles_text.split(",") if normalize_role_code(role)]
    return PortalIdentity(
        subject=subject.strip(),
        email=email.strip(),
        display_name=(display_name or email).strip(),
        roles=roles,
        source=source,
    )


@transaction.atomic
def establish_account_session(identity: PortalIdentity) -> Account:
    account = upsert_account(identity)
    sync_account_roles(account, identity.roles)
    return account


def end_account_session(session_key: str | None) -> None:
    if not session_key:
        return

    now = timezone.now()
    AccountSession.objects.filter(session_key=session_key, ended_at__isnull=True).update(
        ended_at=now,
        last_seen_at=now,
    )


def account_payload(account: Account) -> dict[str, object]:
    return {
        "displayName": account.display_name,
        "email": account.email,
        "portalSubject": account.portal_subject,
        "roles": list(account.roles.values_list("code", flat=True)),
    }


def _get_header(request, *names: str) -> str | None:
    for name in names:
        value = request.headers.get(name)
        if value:
            return value
    return None


def normalize_role_code(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized[:50]


def build_username(subject: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-") or "portal-user"
    digest = hashlib.sha256(subject.encode("utf-8")).hexdigest()[:10]
    trimmed = base[: max(1, 150 - len(digest) - 1)]
    return f"{trimmed}-{digest}"


def split_display_name(display_name: str) -> tuple[str, str]:
    parts = display_name.split(maxsplit=1)
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def upsert_account(identity: PortalIdentity) -> Account:
    now = timezone.now()
    account = Account.objects.select_related("user").filter(portal_subject=identity.subject).first()
    if account is None:
        first_name, last_name = split_display_name(identity.display_name)
        user = User.objects.create(
            username=build_username(identity.subject),
            first_name=first_name,
            last_name=last_name,
            email=identity.email,
            is_active=True,
        )
        account = Account.objects.create(
            user=user,
            portal_subject=identity.subject,
            display_name=identity.display_name,
            email=identity.email,
            is_portal_active=True,
            last_handover_at=now,
            last_seen_at=now,
        )
        return account

    first_name, last_name = split_display_name(identity.display_name)
    user = account.user
    user.first_name = first_name
    user.last_name = last_name
    user.email = identity.email
    user.is_active = True
    user.save(update_fields=["first_name", "last_name", "email", "is_active"])

    account.display_name = identity.display_name
    account.email = identity.email
    account.is_portal_active = True
    account.last_handover_at = now
    account.last_seen_at = now
    account.save(
        update_fields=[
            "display_name",
            "email",
            "is_portal_active",
            "last_handover_at",
            "last_seen_at",
            "updated_at",
        ]
    )
    return account


def sync_account_roles(account: Account, role_codes: list[str]) -> None:
    role_ids: list[int] = []
    for role_code in role_codes:
        role, _ = AppRole.objects.get_or_create(
            code=role_code,
            defaults={"name": role_code.replace("-", " ").title()},
        )
        role_ids.append(role.id)

    account.roles.set(role_ids)


def sync_account_session(request, account: Account, source: str) -> None:
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    if not session_key:
        return

    forwarded_for = request.headers.get("X-Forwarded-For", "")
    remote_addr = forwarded_for.split(",", maxsplit=1)[0].strip() or request.META.get("REMOTE_ADDR")
    AccountSession.objects.update_or_create(
        session_key=session_key,
        defaults={
            "account": account,
            "source": source,
            "user_agent": request.headers.get("User-Agent", "")[:255],
            "remote_addr": remote_addr or None,
            "ended_at": None,
        },
    )
