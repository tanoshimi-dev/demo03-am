from unittest.mock import MagicMock, patch

import jwt as _jwt
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
    def test_portal_mode_redirects_to_portal_login_when_no_cookie(self):
        response = self.client.get("/auth/handover", {"returnTo": "/assets"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://tanoshimi.dev/login?returnTo="))


@override_settings(
    AUTH_MODE="portal",
    PORTAL_JWKS_URL="https://api.tanoshimi.dev/v1/.well-known/jwks.json",
    PORTAL_ISSUER="https://tanoshimi.dev",
    PORTAL_COOKIE_NAMES=["portal_token"],
    PORTAL_LOGIN_URL="https://tanoshimi.dev/login",
    PORTAL_ALLOWED_RETURN_TO_HOSTS=["demo03-am.tanoshimi.dev"],
)
class PortalJWTAuthTests(TestCase):
    _FAKE_CLAIMS = {
        "sub": "portal-jwt-user-001",
        "email": "jwt-user@example.com",
        "name": "JWT User One",
        "roles": ["asset-admin"],
        "iss": "https://tanoshimi.dev",
        "exp": 9_999_999_999,
    }

    def _patch_jwt(self, claims=None):
        """Context manager: mock JWKS client + jwt.decode to return given claims."""
        effective = claims if claims is not None else self._FAKE_CLAIMS
        mock_signing_key = MagicMock()
        jwks_patch = patch("accounts.services._get_jwks_client")
        decode_patch = patch("accounts.services._jwt.decode", return_value=effective)
        return jwks_patch, decode_patch, mock_signing_key

    def test_valid_jwt_cookie_establishes_session(self):
        jwks_patch, decode_patch, mock_signing_key = self._patch_jwt()
        with jwks_patch as mock_get_client, decode_patch:
            mock_get_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key
            self.client.cookies["portal_token"] = "fake.jwt.token"
            response = self.client.get("/auth/handover", {"returnTo": "/"})

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        account = Account.objects.get(portal_subject="portal-jwt-user-001")
        self.assertEqual(account.email, "jwt-user@example.com")
        self.assertCountEqual(account.roles.values_list("code", flat=True), ["asset-admin"])
        session = AccountSession.objects.get(account=account, ended_at__isnull=True)
        self.assertEqual(session.source, AccountSession.SOURCE_PORTAL_JWT)

    def test_jwt_with_single_role_field(self):
        claims = {**self._FAKE_CLAIMS, "role": "sysadmin", "roles": []}
        jwks_patch, decode_patch, mock_signing_key = self._patch_jwt(claims)
        with jwks_patch as mock_get_client, decode_patch:
            mock_get_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key
            self.client.cookies["portal_token"] = "fake.jwt.token"
            response = self.client.get("/auth/handover", {"returnTo": "/"})

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        account = Account.objects.get(portal_subject="portal-jwt-user-001")
        self.assertIn("sysadmin", account.roles.values_list("code", flat=True))

    def test_missing_cookie_redirects_to_portal_login(self):
        response = self.client.get("/auth/handover", {"returnTo": "/"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://tanoshimi.dev/login?returnTo="))

    def test_invalid_jwt_redirects_to_portal_login(self):
        with patch("accounts.services._get_jwks_client") as mock_get_client:
            mock_get_client.return_value.get_signing_key_from_jwt.side_effect = Exception("invalid signature")
            self.client.cookies["portal_token"] = "invalid.jwt.token"
            response = self.client.get("/auth/handover", {"returnTo": "/"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://tanoshimi.dev/login?returnTo="))

    def test_expired_jwt_redirects_to_portal_login(self):
        jwks_patch, _, mock_signing_key = self._patch_jwt()
        with jwks_patch as mock_get_client, \
             patch("accounts.services._jwt.decode", side_effect=_jwt.ExpiredSignatureError("expired")):
            mock_get_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key
            self.client.cookies["portal_token"] = "expired.jwt.token"
            response = self.client.get("/auth/handover", {"returnTo": "/"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://tanoshimi.dev/login?returnTo="))

    @override_settings(PORTAL_JWKS_URL="")
    def test_missing_jwks_url_redirects_to_portal_login(self):
        self.client.cookies["portal_token"] = "some.jwt.token"
        response = self.client.get("/auth/handover", {"returnTo": "/"})

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


class JWTCheckViewTests(TestCase):
    """Tests for /auth/jwt-check diagnostic page."""

    @override_settings(DEBUG=True)
    def test_accessible_in_debug_mode(self):
        response = self.client.get("/auth/jwt-check")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JWT Cookie 診断")

    @override_settings(DEBUG=False)
    def test_forbidden_when_not_debug_and_not_staff(self):
        response = self.client.get("/auth/jwt-check")
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False)
    def test_accessible_to_staff_when_not_debug(self):
        staff = User.objects.create_user("staffuser", is_staff=True, password="pw")
        self.client.force_login(staff)
        response = self.client.get("/auth/jwt-check")
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=True)
    def test_shows_cookie_absent_when_no_cookie(self):
        response = self.client.get("/auth/jwt-check")
        self.assertContains(response, "なし")
        self.assertNotContains(response, "署名検証結果")

    @override_settings(
        DEBUG=True,
        PORTAL_JWKS_URL="https://api.tanoshimi.dev/v1/.well-known/jwks.json",
        PORTAL_ISSUER="https://tanoshimi.dev",
        PORTAL_COOKIE_NAMES=["portal_token"],
    )
    def test_shows_verification_pass_for_valid_jwt(self):
        fake_claims = {
            "sub": "u1",
            "email": "u1@example.com",
            "name": "User One",
            "roles": ["asset-admin"],
            "iss": "https://tanoshimi.dev",
            "exp": 9_999_999_999,
        }
        mock_signing_key = MagicMock()
        with patch("accounts.services._get_jwks_client") as mock_get_client, \
             patch("accounts.services._jwt.decode", return_value=fake_claims), \
             patch("accounts.views._get_jwks_client") as mock_view_client, \
             patch("accounts.views._jwt.decode", return_value=fake_claims), \
             patch("accounts.views._jwt.get_unverified_header", return_value={"alg": "RS256", "kid": "k1"}):
            mock_get_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_view_client.return_value.get_signing_key_from_jwt.return_value = mock_signing_key
            self.client.cookies["portal_token"] = "fake.jwt.token"
            response = self.client.get("/auth/jwt-check")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "検証 PASS")
        self.assertContains(response, "u1@example.com")

    @override_settings(
        DEBUG=True,
        PORTAL_JWKS_URL="https://api.tanoshimi.dev/v1/.well-known/jwks.json",
        PORTAL_ISSUER="https://tanoshimi.dev",
        PORTAL_COOKIE_NAMES=["portal_token"],
    )
    def test_shows_verification_fail_for_invalid_jwt(self):
        with patch("accounts.views._get_jwks_client") as mock_view_client, \
             patch("accounts.views._jwt.get_unverified_header", return_value={"alg": "RS256"}), \
             patch("accounts.views._jwt.decode", return_value={"sub": "u1", "email": "u@x.com", "exp": 9999999999}):
            mock_view_client.return_value.get_signing_key_from_jwt.side_effect = Exception("bad sig")
            self.client.cookies["portal_token"] = "invalid.jwt.token"
            response = self.client.get("/auth/jwt-check")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "検証 FAIL")
        self.assertContains(response, "bad sig")
