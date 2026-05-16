import os
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from config.env import get_bool, get_int, get_list


class EnvHelperTests(SimpleTestCase):
    def test_get_bool_parses_truthy_and_falsy_values(self):
        with patch.dict(os.environ, {"FEATURE_FLAG": " yes ", "OTHER_FLAG": "off"}, clear=False):
            self.assertIs(get_bool("FEATURE_FLAG", False), True)
            self.assertIs(get_bool("OTHER_FLAG", True), False)

    def test_get_bool_raises_for_invalid_value(self):
        with patch.dict(os.environ, {"BROKEN_FLAG": "maybe"}, clear=False):
            with self.assertRaisesMessage(ValueError, "BROKEN_FLAG must be a boolean-like value"):
                get_bool("BROKEN_FLAG", False)

    def test_get_int_and_get_list_use_environment_values(self):
        with patch.dict(os.environ, {"PORT_NUMBER": "18003", "HOSTS": " localhost , 127.0.0.1 ,, "}, clear=False):
            self.assertEqual(get_int("PORT_NUMBER", 80), 18003)
            self.assertEqual(get_list("HOSTS", []), ["localhost", "127.0.0.1"])


class ProjectFoundationTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "demo03_am")
        self.assertContains(response, "/auth/me")

    def test_home_page_shows_key_links(self):
        from accounts.models import Account, AppRole
        from django.contrib.auth.models import User

        admin_user = User.objects.create_user(username="testadmin_home", password="pass")
        admin_role, _ = AppRole.objects.get_or_create(code="asset-admin", defaults={"name": "Asset Admin"})
        account = Account.objects.create(
            user=admin_user,
            portal_subject="test-admin-home",
            display_name="Test Admin",
            email="testadmin@example.com",
        )
        account.roles.add(admin_role)
        self.client.force_login(admin_user)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/assets/")
        self.assertContains(response, "/loans/mine/")
        self.assertContains(response, "/incidents/")
        self.assertContains(response, "/inventory/")
        self.assertContains(response, "/auditlogs/")
