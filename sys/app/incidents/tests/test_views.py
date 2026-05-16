from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory
from incidents.models import IncidentReport
from incidents.services import report_incident


class IncidentViewTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.asset = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            serial_number="SN-0001",
        )
        self.reporter = User.objects.create_user(username="reporter", password="password")

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
        response = self.client.get("/incidents/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/handover", response["Location"])

    def test_non_admin_user_is_redirected_to_assets(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get("/incidents/")

        self.assertRedirects(response, "/assets/")

    def test_admin_can_report_incident(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.post(
            f"/incidents/report/{self.asset.asset_code}/",
            {"incident_type": IncidentReport.TYPE_BREAKDOWN, "description": "起動しない"},
        )

        self.assertRedirects(response, "/incidents/")
        self.asset.refresh_from_db()
        self.assertEqual(IncidentReport.objects.count(), 1)
        self.assertEqual(self.asset.status, Asset.STATUS_IN_REPAIR)

    def test_admin_can_view_incident_list(self):
        self.create_logged_in_account(role_codes=["sysadmin"])
        report_incident(
            asset=self.asset,
            incident_type=IncidentReport.TYPE_LOST,
            reporter=self.reporter,
            description="見当たらない",
        )

        response = self.client.get("/incidents/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "インシデント一覧")
        self.assertContains(response, "ASSET-001")
        self.assertContains(response, "紛失")

    def test_admin_can_resolve_breakdown_incident(self):
        self.create_logged_in_account(role_codes=["asset-admin"])
        report = report_incident(
            asset=self.asset,
            incident_type=IncidentReport.TYPE_BREAKDOWN,
            reporter=self.reporter,
            description="画面が映らない",
        )

        response = self.client.post(
            f"/incidents/{report.pk}/resolve/",
            {"resolution_notes": "部品交換済み"},
        )

        self.assertRedirects(response, "/incidents/")
        report.refresh_from_db()
        self.asset.refresh_from_db()
        self.assertEqual(report.status, IncidentReport.STATUS_RESOLVED)
        self.assertEqual(self.asset.status, Asset.STATUS_IN_STOCK)
