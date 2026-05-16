import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory
from loans.models import LoanRequest
from loans.services import LoanEligibilityError, check_loan_eligibility, create_loan_request


class LoanRequestModelTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.asset = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            status=Asset.STATUS_IN_STOCK,
            serial_number="SN-0001",
        )
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_loan_request_str_includes_username_asset_code_and_status(self):
        req = LoanRequest.objects.create(
            asset=self.asset,
            requester=self.user,
            expected_start_date=datetime.date.today(),
        )

        self.assertIn("testuser", str(req))
        self.assertIn("ASSET-001", str(req))
        self.assertIn("審査中", str(req))

    def test_is_active_for_pending_and_approved_only(self):
        req = LoanRequest(asset=self.asset, requester=self.user,
                          expected_start_date=datetime.date.today())

        for active_status in (LoanRequest.STATUS_PENDING, LoanRequest.STATUS_APPROVED):
            req.status = active_status
            self.assertIs(req.is_active, True)

        for inactive_status in (LoanRequest.STATUS_REJECTED, LoanRequest.STATUS_CANCELLED):
            req.status = inactive_status
            self.assertIs(req.is_active, False)

    def test_default_status_is_pending(self):
        req = LoanRequest.objects.create(
            asset=self.asset,
            requester=self.user,
            expected_start_date=datetime.date.today(),
        )

        self.assertEqual(req.status, LoanRequest.STATUS_PENDING)


class LoanEligibilityServiceTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.asset_in_stock = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            status=Asset.STATUS_IN_STOCK,
            serial_number="SN-0001",
        )
        self.asset_on_loan = Asset.objects.create(
            asset_code="ASSET-002",
            name="ThinkPad X1 Yoga",
            category=self.category,
            status=Asset.STATUS_ON_LOAN,
            serial_number="SN-0002",
        )
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_eligibility_check_raises_for_unavailable_asset(self):
        with self.assertRaises(LoanEligibilityError) as ctx:
            check_loan_eligibility(self.asset_on_loan, self.user)

        self.assertIn("貸出できません", str(ctx.exception))

    def test_eligibility_check_raises_when_active_request_already_exists(self):
        LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=self.user,
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )

        with self.assertRaises(LoanEligibilityError) as ctx:
            check_loan_eligibility(self.asset_in_stock, self.user)

        self.assertIn("未処理の申請", str(ctx.exception))

    def test_eligibility_check_passes_for_available_asset_with_no_active_request(self):
        check_loan_eligibility(self.asset_in_stock, self.user)

    def test_eligibility_check_passes_after_previous_request_was_cancelled(self):
        LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=self.user,
            status=LoanRequest.STATUS_CANCELLED,
            expected_start_date=datetime.date.today(),
        )

        check_loan_eligibility(self.asset_in_stock, self.user)

    def test_create_loan_request_creates_record_on_success(self):
        req = create_loan_request(
            asset=self.asset_in_stock,
            requester=self.user,
            expected_start_date=datetime.date.today(),
        )

        self.assertEqual(req.asset, self.asset_in_stock)
        self.assertEqual(req.requester, self.user)
        self.assertEqual(req.status, LoanRequest.STATUS_PENDING)

    def test_create_loan_request_raises_for_unavailable_asset(self):
        with self.assertRaises(LoanEligibilityError):
            create_loan_request(
                asset=self.asset_on_loan,
                requester=self.user,
                expected_start_date=datetime.date.today(),
            )
