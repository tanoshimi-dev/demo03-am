import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory
from auditlogs.models import AuditLog
from loans.models import LoanRecord, LoanRequest, ReturnRecord
from loans.services import (
    LoanEligibilityError,
    LoanTransitionError,
    approve_loan_request,
    check_loan_eligibility,
    confirm_return,
    create_loan_request,
    reject_loan_request,
    request_return,
)


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


class ApproveRejectServiceTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.asset = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            status=Asset.STATUS_IN_STOCK,
            serial_number="SN-0001",
        )
        self.requester = User.objects.create_user(username="requester", password="p")
        self.approver = User.objects.create_user(username="approver", password="p")
        self.pending_request = LoanRequest.objects.create(
            asset=self.asset,
            requester=self.requester,
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )

    def test_approve_creates_loan_record_and_updates_status(self):
        loan_record = approve_loan_request(
            loan_request=self.pending_request,
            approver=self.approver,
        )

        self.pending_request.refresh_from_db()
        self.asset.refresh_from_db()

        self.assertIsInstance(loan_record, LoanRecord)
        self.assertEqual(self.pending_request.status, LoanRequest.STATUS_APPROVED)
        self.assertEqual(self.asset.status, Asset.STATUS_ON_LOAN)
        self.assertEqual(loan_record.approved_by, self.approver)

    def test_approve_raises_if_not_pending(self):
        self.pending_request.status = LoanRequest.STATUS_APPROVED
        self.pending_request.save()

        with self.assertRaises(LoanTransitionError) as ctx:
            approve_loan_request(loan_request=self.pending_request, approver=self.approver)

        self.assertIn("審査中の状態ではありません", str(ctx.exception))

    def test_approve_raises_if_asset_not_in_stock(self):
        self.asset.status = Asset.STATUS_ON_LOAN
        self.asset.save()

        with self.assertRaises(LoanTransitionError) as ctx:
            approve_loan_request(loan_request=self.pending_request, approver=self.approver)

        self.assertIn("貸出できません", str(ctx.exception))

    def test_reject_sets_status_to_rejected(self):
        reject_loan_request(loan_request=self.pending_request)

        self.pending_request.refresh_from_db()
        self.assertEqual(self.pending_request.status, LoanRequest.STATUS_REJECTED)

    def test_reject_raises_if_not_pending(self):
        self.pending_request.status = LoanRequest.STATUS_APPROVED
        self.pending_request.save()

        with self.assertRaises(LoanTransitionError):
            reject_loan_request(loan_request=self.pending_request)


class ReturnServiceTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.asset = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            status=Asset.STATUS_ON_LOAN,
            serial_number="SN-0001",
        )
        self.requester = User.objects.create_user(username="requester", password="p")
        self.approver = User.objects.create_user(username="approver", password="p")
        self.loan_request = LoanRequest.objects.create(
            asset=self.asset,
            requester=self.requester,
            status=LoanRequest.STATUS_APPROVED,
            expected_start_date=datetime.date.today(),
        )
        self.loan_record = LoanRecord.objects.create(
            loan_request=self.loan_request,
            approved_by=self.approver,
            loan_start_date=datetime.date.today(),
        )

    def test_loan_record_is_on_loan_when_no_return_record(self):
        self.assertIs(self.loan_record.is_on_loan, True)

    def test_request_return_sets_return_requested_at(self):
        request_return(loan_record=self.loan_record)

        self.loan_record.refresh_from_db()
        self.assertIsNotNone(self.loan_record.return_requested_at)

    def test_request_return_raises_if_already_requested(self):
        request_return(loan_record=self.loan_record)

        with self.assertRaises(LoanTransitionError) as ctx:
            request_return(loan_record=self.loan_record)

        self.assertIn("すでに提出", str(ctx.exception))

    def test_confirm_return_creates_return_record_and_restores_asset(self):
        return_record = confirm_return(
            loan_record=self.loan_record,
            receiver=self.approver,
            condition_notes="問題なし",
        )

        self.asset.refresh_from_db()
        self.loan_record.refresh_from_db()

        self.assertIsInstance(return_record, ReturnRecord)
        self.assertEqual(self.asset.status, Asset.STATUS_IN_STOCK)
        self.assertEqual(return_record.condition_notes, "問題なし")
        self.assertIs(self.loan_record.is_on_loan, False)

    def test_confirm_return_raises_if_already_returned(self):
        confirm_return(loan_record=self.loan_record, receiver=self.approver)

        with self.assertRaises(LoanTransitionError) as ctx:
            confirm_return(loan_record=self.loan_record, receiver=self.approver)

        self.assertIn("返却済み", str(ctx.exception))

    def test_full_flow_pending_to_in_stock(self):
        """Integration: pending → approve → request_return → confirm_return."""
        category = AssetCategory.objects.create(code="phone", name="Phone")
        asset = Asset.objects.create(
            asset_code="ASSET-002", name="iPhone", category=category,
            status=Asset.STATUS_IN_STOCK, serial_number="SN-PHONE-01",
        )
        req = LoanRequest.objects.create(
            asset=asset, requester=self.requester,
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )
        loan_record = approve_loan_request(loan_request=req, approver=self.approver)
        asset.refresh_from_db()
        self.assertEqual(asset.status, Asset.STATUS_ON_LOAN)

        request_return(loan_record=loan_record)
        confirm_return(loan_record=loan_record, receiver=self.approver)
        asset.refresh_from_db()
        self.assertEqual(asset.status, Asset.STATUS_IN_STOCK)


class AuditLogIntegrationTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="tablet", name="Tablet")
        self.asset = Asset.objects.create(
            asset_code="TABLET-001",
            name="iPad Air",
            category=self.category,
            status=Asset.STATUS_IN_STOCK,
            serial_number="SN-TABLET-001",
        )
        self.requester = User.objects.create_user(username="audit-requester", password="password")
        self.admin = User.objects.create_user(username="audit-admin", password="password")

    def test_create_request_and_approve_write_audit_logs(self):
        loan_request = create_loan_request(
            asset=self.asset,
            requester=self.requester,
            expected_start_date=datetime.date.today(),
        )
        loan_record = approve_loan_request(loan_request=loan_request, approver=self.admin)

        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_LOAN_REQUESTED,
                actor=self.requester,
                asset_code=self.asset.asset_code,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_LOAN_APPROVED,
                actor=self.admin,
                asset_code=self.asset.asset_code,
                object_repr=str(loan_record),
            ).exists()
        )

    def test_reject_and_return_flow_write_audit_logs(self):
        rejected_request = create_loan_request(
            asset=self.asset,
            requester=self.requester,
            expected_start_date=datetime.date.today(),
        )
        reject_loan_request(loan_request=rejected_request, rejector=self.admin)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_LOAN_REJECTED,
                actor=self.admin,
                asset_code=self.asset.asset_code,
            ).exists()
        )

        second_asset = Asset.objects.create(
            asset_code="TABLET-002",
            name="Surface Go",
            category=self.category,
            status=Asset.STATUS_IN_STOCK,
            serial_number="SN-TABLET-002",
        )
        approved_request = create_loan_request(
            asset=second_asset,
            requester=self.requester,
            expected_start_date=datetime.date.today(),
        )
        loan_record = approve_loan_request(loan_request=approved_request, approver=self.admin)

        request_return(loan_record=loan_record)
        confirm_return(loan_record=loan_record, receiver=self.admin)

        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_RETURN_REQUESTED,
                actor__isnull=True,
                asset_code=second_asset.asset_code,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_RETURN_CONFIRMED,
                actor=self.admin,
                asset_code=second_asset.asset_code,
            ).exists()
        )
