from django.conf import settings

from .models import Account

_MANAGE_ROLES = {"asset-admin", "sysadmin"}


def demo_context(request):
    auth_mode = getattr(settings, "AUTH_MODE", "")
    account = getattr(request, "account", None)

    role_codes = set(account.roles.values_list("code", flat=True)) if account else set()
    can_manage = bool(role_codes & _MANAGE_ROLES)

    if auth_mode != "dev-header":
        return {
            "auth_mode": auth_mode,
            "debug": settings.DEBUG,
            "demo_accounts": [],
            "current_account": account,
            "can_manage": can_manage,
        }

    subjects = getattr(settings, "DEMO_SWITCH_SUBJECTS", [])
    demo_accounts = list(Account.objects.filter(portal_subject__in=subjects).select_related())
    subject_order = {subject: index for index, subject in enumerate(subjects)}
    demo_accounts.sort(key=lambda a: subject_order.get(a.portal_subject, 999))

    return {
        "auth_mode": auth_mode,
        "debug": settings.DEBUG,
        "demo_accounts": demo_accounts,
        "current_account": account,
        "can_manage": can_manage,
    }
