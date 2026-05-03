from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings

from accounts.models import Account, AccountSession, AppRole
from accounts.services import build_portal_login_url, sanitize_return_to


class AuthFlowTests(TestCase):
    def test_auth_me_returns_handover_url_when_unauthenticated(self):
        response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "authenticated": False,
                "authMode": "dev-header",
                "handoverUrl": "/auth/handover?returnTo=/",
            },
        )

    def test_handover_creates_account_roles_and_session(self):
        response = self.client.get(
            "/auth/handover",
            {"returnTo": "/auth/me"},
            HTTP_X_PORTAL_SUBJECT="portal-user-001",
            HTTP_X_PORTAL_EMAIL="user1@example.com",
            HTTP_X_PORTAL_NAME="Demo User One",
            HTTP_X_PORTAL_ROLES="asset-admin, employee",
        )

        self.assertRedirects(response, "/auth/me", fetch_redirect_response=False)

        me_response = self.client.get("/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(
            me_response.json()["user"],
            {
                "displayName": "Demo User One",
                "email": "user1@example.com",
                "portalSubject": "portal-user-001",
                "roles": ["asset-admin", "employee"],
            },
        )

        account = Account.objects.get(portal_subject="portal-user-001")
        self.assertEqual(account.user.email, "user1@example.com")
        self.assertCountEqual(account.roles.values_list("code", flat=True), ["asset-admin", "employee"])

        session = AccountSession.objects.get(account=account, ended_at__isnull=True)
        self.assertEqual(session.source, AccountSession.SOURCE_DEV_HEADER)
        self.assertTrue(self.client.session.session_key)
        self.assertEqual(session.session_key, self.client.session.session_key)

    def test_logout_ends_local_account_session(self):
        self.client.get(
            "/auth/handover",
            {"returnTo": "/"},
            HTTP_X_PORTAL_SUBJECT="portal-user-002",
            HTTP_X_PORTAL_EMAIL="user2@example.com",
            HTTP_X_PORTAL_NAME="Demo User Two",
        )
        session_key = self.client.session.session_key

        response = self.client.get("/auth/logout", {"returnTo": "/"})

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.assertIsNotNone(AccountSession.objects.get(session_key=session_key).ended_at)

    @override_settings(AUTH_MODE="portal", PORTAL_LOGIN_URL="https://tanoshimi.dev/login")
    def test_portal_mode_redirects_to_portal_login_when_headers_not_trusted(self):
        response = self.client.get(
            "/auth/handover",
            {"returnTo": "/assets"},
            HTTP_X_PORTAL_SUBJECT="portal-user-003",
            HTTP_X_PORTAL_EMAIL="user3@example.com",
            HTTP_X_PORTAL_NAME="Demo User Three",
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://tanoshimi.dev/login?returnTo="))


class ReturnToSanitizationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_sanitize_return_to_allows_local_path_and_known_host(self):
        request = self.factory.get("/", HTTP_HOST="localhost:18003")

        self.assertEqual(sanitize_return_to(request, "/assets"), "/assets")
        self.assertEqual(
            sanitize_return_to(request, "http://localhost:18003/assets"),
            "http://localhost:18003/assets",
        )

    def test_sanitize_return_to_rejects_unknown_host(self):
        request = self.factory.get("/", HTTP_HOST="localhost:18003")

        self.assertEqual(sanitize_return_to(request, "http://evil.example/assets"), "/")

    @override_settings(PORTAL_LOGIN_URL="https://tanoshimi.dev/login")
    def test_build_portal_login_url_uses_absolute_return_to(self):
        request = self.factory.get("/", HTTP_HOST="localhost:18003")

        url = build_portal_login_url(request, "/assets")

        self.assertEqual(url, "https://tanoshimi.dev/login?returnTo=http%3A%2F%2Flocalhost%3A18003%2Fassets")


class AccountModelTests(TestCase):
    def test_account_string_representation_uses_display_name_and_subject(self):
        user = User.objects.create(username="demo-user")
        account = Account.objects.create(
            user=user,
            portal_subject="portal-user-004",
            display_name="Demo User Four",
            email="user4@example.com",
        )
        AppRole.objects.create(code="employee", name="Employee")

        self.assertEqual(str(account), "Demo User Four (portal-user-004)")
