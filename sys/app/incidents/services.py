from django.db import transaction
from django.utils import timezone

from assets.models import Asset
from auditlogs.models import AuditLog
from auditlogs.services import log_action

from .models import IncidentReport


class IncidentError(Exception):
    pass


@transaction.atomic
def report_incident(asset: Asset, incident_type: str, reporter, description: str = "") -> IncidentReport:
    valid_types = {
        IncidentReport.TYPE_BREAKDOWN,
        IncidentReport.TYPE_LOST,
        IncidentReport.TYPE_RETIRED,
    }
    if incident_type not in valid_types:
        raise IncidentError("不正なインシデント種別です。")

    if asset.status == Asset.STATUS_RETIRED:
        raise IncidentError("廃棄済みの資産にインシデントを報告することはできません。")
    if asset.status == Asset.STATUS_LOST and incident_type == IncidentReport.TYPE_LOST:
        raise IncidentError("この資産はすでに紛失報告済みです。")

    status_map = {
        IncidentReport.TYPE_BREAKDOWN: Asset.STATUS_IN_REPAIR,
        IncidentReport.TYPE_LOST: Asset.STATUS_LOST,
        IncidentReport.TYPE_RETIRED: Asset.STATUS_RETIRED,
    }
    report = IncidentReport.objects.create(
        asset=asset,
        incident_type=incident_type,
        description=description,
        reported_by=reporter,
    )
    asset.status = status_map[incident_type]
    asset.save(update_fields=["status", "updated_at"])
    log_action(
        AuditLog.ACTION_INCIDENT_REPORTED,
        actor=reporter,
        asset_code=asset.asset_code,
        object_repr=str(report),
        extra={"incident_type": incident_type},
    )
    return report


@transaction.atomic
def resolve_incident(
    incident_report: IncidentReport,
    resolver,
    resolution_notes: str = "",
) -> IncidentReport:
    if incident_report.status == IncidentReport.STATUS_RESOLVED:
        raise IncidentError("このインシデントはすでに解決済みです。")
    if incident_report.incident_type != IncidentReport.TYPE_BREAKDOWN:
        raise IncidentError("故障以外のインシデントは解決処理できません。")

    incident_report.status = IncidentReport.STATUS_RESOLVED
    incident_report.resolved_by = resolver
    incident_report.resolved_at = timezone.now()
    incident_report.resolution_notes = resolution_notes
    incident_report.save(
        update_fields=[
            "status",
            "resolved_by",
            "resolved_at",
            "resolution_notes",
            "updated_at",
        ]
    )

    asset = incident_report.asset
    asset.status = Asset.STATUS_IN_STOCK
    asset.save(update_fields=["status", "updated_at"])
    log_action(
        AuditLog.ACTION_INCIDENT_RESOLVED,
        actor=resolver,
        asset_code=incident_report.asset.asset_code,
        object_repr=str(incident_report),
    )
    return incident_report
