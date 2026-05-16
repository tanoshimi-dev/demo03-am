from django.contrib.auth.models import User

from assets.models import Asset

from .models import LoanRequest


class LoanEligibilityError(Exception):
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
