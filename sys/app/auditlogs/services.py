from .models import AuditLog


def log_action(
    action: str,
    actor,
    asset_code: str = "",
    object_repr: str = "",
    extra: dict | None = None,
) -> AuditLog:
    """Create an AuditLog entry in the same transaction as the domain action."""
    return AuditLog.objects.create(
        action=action,
        actor=actor,
        asset_code=asset_code,
        object_repr=object_repr,
        extra=extra or {},
    )
