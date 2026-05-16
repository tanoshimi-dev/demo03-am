from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Account, AppRole
from auditlogs.models import AuditLog


class AuditLogViewTests(TestCase):
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

    def setUp(self):
        self.actor = User.objects.create_user(username="actor", password="password")
        AuditLog.objects.create(
            action=AuditLog.ACTION_LOAN_APPROVED,
            actor=self.actor,
            asset_code="LAPTOP-001",
            object_repr="loan-1",
        )
        AuditLog.objects.create(
            action=AuditLog.ACTION_INCIDENT_REPORTED,
            actor=self.actor,
            asset_code="PHONE-002",
            object_repr="incident-1",
        )

    def test_unauthenticated_redirected(self):
        response = self.client.get("/auditlogs/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/handover", response["Location"])

    def test_non_admin_redirected(self):
        self.create_logged_in_account(role_codes=["employee"])

        response = self.client.get("/auditlogs/")

        self.assertRedirects(response, "/assets/")

    def test_admin_can_view_auditlog_list(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.get("/auditlogs/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "監査ログ")
        self.assertContains(response, "LAPTOP-001")
        self.assertContains(response, "PHONE-002")

    def test_admin_can_filter_by_action(self):
        self.create_logged_in_account(role_codes=["sysadmin"])

        response = self.client.get("/auditlogs/", {"action": AuditLog.ACTION_LOAN_APPROVED})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LAPTOP-001")
        self.assertNotContains(response, "PHONE-002")

    def test_admin_can_filter_by_asset_code(self):
        self.create_logged_in_account(role_codes=["asset-admin"])

        response = self.client.get("/auditlogs/", {"asset_code": "PHONE"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PHONE-002")
        self.assertNotContains(response, "LAPTOP-001")
