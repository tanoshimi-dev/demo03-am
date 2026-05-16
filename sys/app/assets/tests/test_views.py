from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory


class AssetViewTests(TestCase):
    def setUp(self):
        self.laptop = AssetCategory.objects.create(code="laptop", name="Laptop", sort_order=10)
        self.monitor = AssetCategory.objects.create(code="monitor", name="Monitor", sort_order=20)
        self.asset_one = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.laptop,
            status=Asset.STATUS_IN_STOCK,
            serial_number="SN-0001",
            manufacturer="Lenovo",
            model_name="X1 Carbon",
            location="HQ Cabinet A",
        )
        self.asset_two = Asset.objects.create(
            asset_code="ASSET-002",
            name='Dell 27" Monitor',
            category=self.monitor,
            status=Asset.STATUS_ON_LOAN,
            serial_number="SN-0002",
            manufacturer="Dell",
            model_name="U2723QE",
            location="Meeting Room",
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

    def test_asset_list_redirects_unauthenticated_users_to_handover(self):
        response = self.client.get("/assets/?q=laptop")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/auth/handover?returnTo=%2Fassets%2F%3Fq%3Dlaptop")

    def test_asset_list_renders_for_regular_user(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get("/assets/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "資産一覧")
        self.assertContains(response, '/static/styles/app.css')
        self.assertContains(response, "ThinkPad X1 Carbon")
        self.assertContains(response, "利用者向け表示")
        self.assertNotContains(response, "管理者向け表示")

    def test_asset_list_shows_management_section_for_asset_admin(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.get("/assets/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "管理者向け表示")
        self.assertContains(response, "/admin/assets/asset/")

    def test_asset_list_filters_by_search_status_and_category(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get("/assets/", {"q": "Monitor", "status": Asset.STATUS_ON_LOAN, "category": "monitor"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dell 27&quot; Monitor', html=False)
        self.assertNotContains(response, "ThinkPad X1 Carbon")

    def test_asset_detail_renders_asset_information(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get(f"/assets/{self.asset_one.asset_code}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/static/styles/app.css')
        self.assertContains(response, "ThinkPad X1 Carbon")
        self.assertContains(response, "貸出可能")
        self.assertContains(response, "利用者向け表示")

    def test_asset_detail_shows_management_section_for_admin(self):
        self.create_logged_in_account(role_codes=["sysadmin"])

        response = self.client.get(f"/assets/{self.asset_two.asset_code}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "管理者向け表示")
        self.assertContains(response, "カテゴリ、状態、保管場所の更新は Django Admin から行えます。")

    def test_asset_detail_shows_incident_report_link_for_admin(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.get(f"/assets/{self.asset_one.asset_code}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "インシデント報告")
        self.assertContains(response, f"/incidents/report/{self.asset_one.asset_code}/")
