from django.db import transaction
from django.utils import timezone

from assets.models import Asset

from .models import InventoryResult, InventorySession


class InventoryError(Exception):
    pass


def open_inventory_session(name: str, created_by, notes: str = "") -> InventorySession:
    return InventorySession.objects.create(name=name, created_by=created_by, notes=notes)


@transaction.atomic
def record_inventory_result(
    session: InventorySession,
    asset: Asset,
    status: str,
    recorded_by,
    notes: str = "",
) -> InventoryResult:
    if session.status == InventorySession.STATUS_CLOSED:
        raise InventoryError("完了済みの棚卸しセッションには結果を入力できません。")
    valid_statuses = {
        InventoryResult.STATUS_CONFIRMED,
        InventoryResult.STATUS_MISSING,
    }
    if status not in valid_statuses:
        raise InventoryError("不正な結果ステータスです。")
    result, _ = InventoryResult.objects.update_or_create(
        session=session,
        asset=asset,
        defaults={"status": status, "notes": notes, "recorded_by": recorded_by},
    )
    return result


@transaction.atomic
def close_inventory_session(session: InventorySession, closed_by) -> InventorySession:
    if session.status == InventorySession.STATUS_CLOSED:
        raise InventoryError("このセッションはすでに完了しています。")
    session.status = InventorySession.STATUS_CLOSED
    session.closed_by = closed_by
    session.closed_at = timezone.now()
    session.save(update_fields=["status", "closed_by", "closed_at", "updated_at"])
    return session


def get_discrepancies(session: InventorySession):
    return session.results.filter(
        status=InventoryResult.STATUS_MISSING,
        asset__status=Asset.STATUS_IN_STOCK,
    ).select_related("asset", "asset__category", "recorded_by")
