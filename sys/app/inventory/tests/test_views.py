from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory
from inventory.models import InventoryResult, InventorySession


class InventoryViewTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.asset = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            serial_number="SN-0001",
        )

    def create_logged_in_account(self, role_codes: list[str] | None = None) -> Account:
        user = User.objects.create_user(username=f"user-{User.objects.count() + 1}", password="password")
        account = Account.objects.create(
            user=user,
            portal_subject=f"portal-{user.username}",
            display_name=f"Display {user.username}",
            email=f"{user.username}@example.com",
        )
        for role_code in role_codes or []:
            role, _ = AppRole.objects.get_or_create(code=role_code, defaults={"name": role_code.title()})
            account.roles.add(role)
        self.client.force_login(user)
        return account

    def test_unauthenticated_user_is_redirected_to_handover(self):
        response = self.client.get("/inventory/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/handover", response["Location"])

    def test_non_admin_user_is_redirected_to_assets(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get("/inventory/")

        self.assertRedirects(response, "/assets/")

    def test_admin_can_create_session(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.post(
            "/inventory/new/",
            {"name": "2026Q2 棚卸し", "notes": "demo"},
        )

        session = InventorySession.objects.get()
        self.assertRedirects(response, f"/inventory/{session.pk}/")
        self.assertEqual(session.status, InventorySession.STATUS_OPEN)

    def test_admin_can_view_session_list(self):
        account = self.create_logged_in_account(role_codes=["asset-admin"])
        InventorySession.objects.create(name="2026Q1 棚卸し", created_by=account.user)
        InventorySession.objects.create(name="2026Q2 棚卸し", created_by=account.user)

        response = self.client.get("/inventory/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026Q1 棚卸し")
        self.assertContains(response, "2026Q2 棚卸し")

    def test_admin_can_view_session_detail(self):
        account = self.create_logged_in_account(role_codes=["sysadmin"])
        session = InventorySession.objects.create(name="2026Q2", created_by=account.user)

        response = self.client.get(f"/inventory/{session.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026Q2")
        self.assertContains(response, "実査結果を入力")

    def test_admin_can_record_result(self):
        account = self.create_logged_in_account(role_codes=["asset-admin"])
        session = InventorySession.objects.create(name="2026Q2", created_by=account.user)

        response = self.client.post(
            f"/inventory/{session.pk}/record/{self.asset.asset_code}/",
            {"status": InventoryResult.STATUS_CONFIRMED, "notes": "確認済み"},
        )

        self.assertRedirects(response, f"/inventory/{session.pk}/")
        result = InventoryResult.objects.get()
        self.assertEqual(result.asset, self.asset)
        self.assertEqual(result.status, InventoryResult.STATUS_CONFIRMED)

    def test_admin_can_close_session(self):
        account = self.create_logged_in_account(role_codes=["asset-admin"])
        session = InventorySession.objects.create(name="2026Q2", created_by=account.user)

        response = self.client.post(f"/inventory/{session.pk}/close/")

        self.assertRedirects(response, f"/inventory/{session.pk}/")
        session.refresh_from_db()
        self.assertEqual(session.status, InventorySession.STATUS_CLOSED)
        self.assertIsNotNone(session.closed_at)
