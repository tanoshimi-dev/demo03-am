import datetime

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from assets.models import Asset

from .models import LoanRecord, LoanRequest, ReturnRecord


class LoanEligibilityError(Exception):
    pass


class LoanTransitionError(Exception):
    pass


def check_loan_eligibility(asset: Asset, requester: User) -> None:
    """Raise LoanEligibilityError if the loan request cannot proceed."""
    if not asset.is_available_for_loan:
        raise LoanEligibilityError(
            f"資産「{asset.name}」は現在貸出できません（状態: {asset.get_status_display()}）。"
        )
    if LoanRequest.objects.filter(
        asset=asset,
        requester=requester,
        status__in=[LoanRequest.STATUS_PENDING, LoanRequest.STATUS_APPROVED],
    ).exists():
        raise LoanEligibilityError(
            f"資産「{asset.name}」にはすでに未処理の申請があります。"
        )


def create_loan_request(asset: Asset, requester: User, **kwargs) -> LoanRequest:
    """Check eligibility and create a LoanRequest."""
    check_loan_eligibility(asset, requester)
    return LoanRequest.objects.create(asset=asset, requester=requester, **kwargs)


@transaction.atomic
def approve_loan_request(
    loan_request: LoanRequest,
    approver: User,
    loan_start_date: datetime.date | None = None,
    expected_return_date: datetime.date | None = None,
) -> LoanRecord:
    """Approve a pending loan request: create LoanRecord, update asset status."""
    if loan_request.status != LoanRequest.STATUS_PENDING:
        raise LoanTransitionError("この申請は審査中の状態ではありません。")
    asset = loan_request.asset
    if not asset.is_available_for_loan:
        raise LoanTransitionError(
            f"資産「{asset.name}」は現在貸出できません（状態: {asset.get_status_display()}）。"
        )
    if loan_start_date is None:
        loan_start_date = datetime.date.today()
    if expected_return_date is None:
        expected_return_date = loan_request.expected_return_date

    loan_record = LoanRecord.objects.create(
        loan_request=loan_request,
        approved_by=approver,
        loan_start_date=loan_start_date,
        expected_return_date=expected_return_date,
    )
    loan_request.status = LoanRequest.STATUS_APPROVED
    loan_request.save(update_fields=["status", "updated_at"])
    asset.status = Asset.STATUS_ON_LOAN
    asset.save(update_fields=["status", "updated_at"])
    return loan_record


@transaction.atomic
def reject_loan_request(loan_request: LoanRequest) -> LoanRequest:
    """Reject a pending loan request."""
    if loan_request.status != LoanRequest.STATUS_PENDING:
        raise LoanTransitionError("この申請は審査中の状態ではありません。")
    loan_request.status = LoanRequest.STATUS_REJECTED
    loan_request.save(update_fields=["status", "updated_at"])
    return loan_request


@transaction.atomic
def request_return(loan_record: LoanRecord) -> LoanRecord:
    """Record a return request from the borrower."""
    if not loan_record.is_on_loan:
        raise LoanTransitionError("この貸出はすでに返却済みです。")
    if loan_record.return_requested_at is not None:
        raise LoanTransitionError("返却申請はすでに提出されています。")
    loan_record.return_requested_at = timezone.now()
    loan_record.save(update_fields=["return_requested_at", "updated_at"])
    return loan_record


@transaction.atomic
def confirm_return(
    loan_record: LoanRecord,
    receiver: User,
    condition_notes: str = "",
) -> ReturnRecord:
    """Confirm return: create ReturnRecord and restore asset to in_stock."""
    if not loan_record.is_on_loan:
        raise LoanTransitionError("この貸出はすでに返却済みです。")
    return_record = ReturnRecord.objects.create(
        loan_record=loan_record,
        received_by=receiver,
        returned_at=timezone.now(),
        condition_notes=condition_notes,
    )
    asset = loan_record.loan_request.asset
    if asset.status == Asset.STATUS_ON_LOAN:
        asset.status = Asset.STATUS_IN_STOCK
        asset.save(update_fields=["status", "updated_at"])
    return return_record
