import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory
from loans.models import LoanRecord, LoanRequest, ReturnRecord
from loans.services import approve_loan_request, confirm_return, request_return


class LoanViewTestBase(TestCase):
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

    def create_logged_in_account(self, role_codes: list[str] | None = None) -> Account:
        user = User.objects.create_user(
            username=f"user-{User.objects.count() + 1}", password="password"
        )
        account = Account.objects.create(
            user=user,
            portal_subject=f"portal-{user.username}",
            display_name=f"Display {user.username}",
            email=f"{user.username}@example.com",
        )
        for code in role_codes or []:
            role, _ = AppRole.objects.get_or_create(code=code, defaults={"name": code.title()})
            account.roles.add(role)
        self.client.force_login(user)
        return account


class LoanRequestCreateViewTests(LoanViewTestBase):
    def test_unauthenticated_user_is_redirected_to_handover(self):
        response = self.client.get(f"/loans/request/{self.asset_in_stock.asset_code}/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/handover", response["Location"])

    def test_form_renders_for_available_asset(self):
        self.create_logged_in_account()

        response = self.client.get(f"/loans/request/{self.asset_in_stock.asset_code}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "貸出申請")
        self.assertContains(response, "ASSET-001")
        self.assertContains(response, "申請する")

    def test_form_shows_unavailable_notice_for_non_stock_asset(self):
        self.create_logged_in_account()

        response = self.client.get(f"/loans/request/{self.asset_on_loan.asset_code}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "現在貸出できません")
        self.assertNotContains(response, "申請する")

    def test_successful_post_creates_loan_request_and_redirects(self):
        self.create_logged_in_account()

        response = self.client.post(
            f"/loans/request/{self.asset_in_stock.asset_code}/",
            {
                "expected_start_date": "2026-06-01",
                "expected_return_date": "2026-06-30",
                "purpose": "業務用",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/loans/mine/")
        self.assertEqual(LoanRequest.objects.count(), 1)
        req = LoanRequest.objects.get()
        self.assertEqual(req.asset, self.asset_in_stock)
        self.assertEqual(req.status, LoanRequest.STATUS_PENDING)

    def test_post_rejects_request_for_unavailable_asset(self):
        self.create_logged_in_account()

        response = self.client.post(
            f"/loans/request/{self.asset_on_loan.asset_code}/",
            {
                "expected_start_date": "2026-06-01",
                "purpose": "業務用",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "現在貸出できません")
        self.assertEqual(LoanRequest.objects.count(), 0)

    def test_post_rejects_duplicate_pending_request(self):
        account = self.create_logged_in_account()
        LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=account.user,
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )

        response = self.client.post(
            f"/loans/request/{self.asset_in_stock.asset_code}/",
            {
                "expected_start_date": "2026-06-01",
                "purpose": "業務用",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "未処理の申請")
        self.assertEqual(LoanRequest.objects.count(), 1)

    def test_date_validation_rejects_return_before_start(self):
        self.create_logged_in_account()

        response = self.client.post(
            f"/loans/request/{self.asset_in_stock.asset_code}/",
            {
                "expected_start_date": "2026-06-30",
                "expected_return_date": "2026-06-01",
                "purpose": "業務用",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "返却予定日は利用開始予定日以降にしてください")
        self.assertEqual(LoanRequest.objects.count(), 0)


class MyLoanListViewTests(LoanViewTestBase):
    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get("/loans/mine/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/handover", response["Location"])

    def test_shows_only_own_loan_requests(self):
        account_a = self.create_logged_in_account()
        other_user = User.objects.create_user(username="other", password="password")
        LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=account_a.user,
            expected_start_date=datetime.date.today(),
        )
        LoanRequest.objects.create(
            asset=self.asset_on_loan,
            requester=other_user,
            expected_start_date=datetime.date.today(),
        )

        response = self.client.get("/loans/mine/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "自分の貸出申請")
        self.assertContains(response, "ASSET-001")
        self.assertNotContains(response, "ASSET-002")

    def test_empty_state_shows_no_requests_message(self):
        self.create_logged_in_account()

        response = self.client.get("/loans/mine/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "貸出申請はありません")

    def test_shows_return_request_button_for_approved_loan(self):
        account = self.create_logged_in_account()
        approver = User.objects.create_user(username="approver", password="p")
        req = LoanRequest.objects.create(
            asset=self.asset_on_loan,
            requester=account.user,
            status=LoanRequest.STATUS_APPROVED,
            expected_start_date=datetime.date.today(),
        )
        LoanRecord.objects.create(
            loan_request=req,
            approved_by=approver,
            loan_start_date=datetime.date.today(),
        )

        response = self.client.get("/loans/mine/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "返却申請")


class LoanRequestAdminListViewTests(LoanViewTestBase):
    def test_regular_user_is_redirected_to_my_list(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get("/loans/admin/")

        self.assertRedirects(response, "/loans/mine/")

    def test_asset_admin_can_access_admin_list(self):
        self.create_logged_in_account(role_codes=["asset-admin"])
        LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=User.objects.create_user(username="emp", password="p"),
            expected_start_date=datetime.date.today(),
        )

        response = self.client.get("/loans/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "貸出申請")
        self.assertContains(response, "ASSET-001")

    def test_admin_list_shows_approve_reject_buttons_for_pending(self):
        self.create_logged_in_account(role_codes=["asset-admin"])
        LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=User.objects.create_user(username="emp", password="p"),
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )

        response = self.client.get("/loans/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "承認")
        self.assertContains(response, "却下")

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get("/loans/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/handover", response["Location"])


class LoanApproveViewTests(LoanViewTestBase):
    def setUp(self):
        super().setUp()
        self.emp = User.objects.create_user(username="emp", password="p")
        self.pending_req = LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=self.emp,
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )

    def test_admin_can_approve_pending_request(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.post(f"/loans/admin/{self.pending_req.pk}/approve/")

        self.assertRedirects(response, "/loans/admin/")
        self.pending_req.refresh_from_db()
        self.asset_in_stock.refresh_from_db()
        self.assertEqual(self.pending_req.status, LoanRequest.STATUS_APPROVED)
        self.assertEqual(self.asset_in_stock.status, Asset.STATUS_ON_LOAN)

    def test_regular_user_cannot_approve(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.post(f"/loans/admin/{self.pending_req.pk}/approve/")

        self.assertRedirects(response, "/loans/mine/")
        self.pending_req.refresh_from_db()
        self.assertEqual(self.pending_req.status, LoanRequest.STATUS_PENDING)


class LoanRejectViewTests(LoanViewTestBase):
    def setUp(self):
        super().setUp()
        self.emp = User.objects.create_user(username="emp", password="p")
        self.pending_req = LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=self.emp,
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )

    def test_admin_can_reject_pending_request(self):
        self.create_logged_in_account(role_codes=["sysadmin"])

        response = self.client.post(f"/loans/admin/{self.pending_req.pk}/reject/")

        self.assertRedirects(response, "/loans/admin/")
        self.pending_req.refresh_from_db()
        self.assertEqual(self.pending_req.status, LoanRequest.STATUS_REJECTED)


class ReturnRequestViewTests(LoanViewTestBase):
    def setUp(self):
        super().setUp()
        self.account = None
        self.approver = User.objects.create_user(username="approver", password="p")

    def _setup_active_loan(self) -> LoanRecord:
        self.account = self.create_logged_in_account()
        req = LoanRequest.objects.create(
            asset=self.asset_on_loan,
            requester=self.account.user,
            status=LoanRequest.STATUS_APPROVED,
            expected_start_date=datetime.date.today(),
        )
        return LoanRecord.objects.create(
            loan_request=req,
            approved_by=self.approver,
            loan_start_date=datetime.date.today(),
        )

    def test_user_can_submit_return_request(self):
        loan_record = self._setup_active_loan()

        response = self.client.post(f"/loans/mine/{loan_record.pk}/return-request/")

        self.assertRedirects(response, "/loans/mine/")
        loan_record.refresh_from_db()
        self.assertIsNotNone(loan_record.return_requested_at)

    def test_user_cannot_submit_return_request_for_others_loan(self):
        other_user = User.objects.create_user(username="other", password="p")
        req = LoanRequest.objects.create(
            asset=self.asset_on_loan,
            requester=other_user,
            status=LoanRequest.STATUS_APPROVED,
            expected_start_date=datetime.date.today(),
        )
        loan_record = LoanRecord.objects.create(
            loan_request=req, approved_by=self.approver,
            loan_start_date=datetime.date.today(),
        )
        self.create_logged_in_account()

        response = self.client.post(f"/loans/mine/{loan_record.pk}/return-request/")

        self.assertEqual(response.status_code, 404)


class ReturnConfirmViewTests(LoanViewTestBase):
    def setUp(self):
        super().setUp()
        self.emp = User.objects.create_user(username="emp", password="p")
        self.approver_user = User.objects.create_user(username="approver_u", password="p")
        req = LoanRequest.objects.create(
            asset=self.asset_on_loan,
            requester=self.emp,
            status=LoanRequest.STATUS_APPROVED,
            expected_start_date=datetime.date.today(),
        )
        self.loan_record = LoanRecord.objects.create(
            loan_request=req,
            approved_by=self.approver_user,
            loan_start_date=datetime.date.today(),
        )

    def test_admin_sees_return_confirm_form(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.get(f"/loans/admin/return-confirm/{self.loan_record.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "返却確認")

    def test_admin_can_confirm_return(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.post(
            f"/loans/admin/return-confirm/{self.loan_record.pk}/",
            {"condition_notes": "良好"},
        )

        self.assertRedirects(response, "/loans/admin/")
        self.asset_on_loan.refresh_from_db()
        self.assertEqual(self.asset_on_loan.status, Asset.STATUS_IN_STOCK)
        self.assertTrue(ReturnRecord.objects.filter(loan_record=self.loan_record).exists())

    def test_regular_user_cannot_access_return_confirm(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get(f"/loans/admin/return-confirm/{self.loan_record.pk}/")

        self.assertRedirects(response, "/loans/mine/")
