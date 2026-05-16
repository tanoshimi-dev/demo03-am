import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory
from loans.models import LoanRequest


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
        self.assertContains(response, "貸出申請一覧")
        self.assertContains(response, "ASSET-001")

    def test_sysadmin_can_filter_by_status(self):
        self.create_logged_in_account(role_codes=["sysadmin"])
        emp = User.objects.create_user(username="emp", password="p")
        LoanRequest.objects.create(
            asset=self.asset_in_stock,
            requester=emp,
            status=LoanRequest.STATUS_PENDING,
            expected_start_date=datetime.date.today(),
        )

        response = self.client.get("/loans/admin/", {"status": LoanRequest.STATUS_APPROVED})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "ASSET-001")

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get("/loans/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/handover", response["Location"])
