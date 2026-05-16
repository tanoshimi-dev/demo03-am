from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings

from accounts.context_processors import demo_context
from accounts.models import Account, AccountSession, AppRole


@override_settings(
    AUTH_MODE="dev-header",
    DEMO_SWITCH_SUBJECTS=["portal-demo-employee", "portal-demo-admin"],
)
class DemoSwitchViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.asset_admin_role = AppRole.objects.create(code="asset-admin", name="Asset Admin")

        self.demo_employee_user = User.objects.create_user(
            username="demo_employee",
            password="demo1234",
            first_name="Demo",
            last_name="Employee",
            email="demo_employee@example.com",
        )
        self.demo_employee = Account.objects.create(
            user=self.demo_employee_user,
            portal_subject="portal-demo-employee",
            display_name="Demo Employee",
            email="demo_employee@example.com",
        )

        self.demo_admin_user = User.objects.create_user(
            username="demo_admin",
            password="demo1234",
            first_name="Demo",
            last_name="Admin",
            email="demo_admin@example.com",
            is_staff=True,
            is_superuser=True,
        )
        self.demo_admin = Account.objects.create(
            user=self.demo_admin_user,
            portal_subject="portal-demo-admin",
            display_name="Demo Admin",
            email="demo_admin@example.com",
        )
        self.demo_admin.roles.add(self.asset_admin_role)

    def test_switch_success_employee(self):
        response = self.client.post(
            "/auth/demo-switch",
            {"portal_subject": "portal-demo-employee", "returnTo": "/"},
        )

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.demo_employee_user.pk)
        session = AccountSession.objects.get(session_key=self.client.session.session_key, ended_at__isnull=True)
        self.assertEqual(session.account, self.demo_employee)
        self.assertEqual(session.source, AccountSession.SOURCE_DEV_HEADER)

    def test_switch_success_admin(self):
        response = self.client.post(
            "/auth/demo-switch",
            {"portal_subject": "portal-demo-admin", "returnTo": "/auth/me"},
        )

        self.assertRedirects(response, "/auth/me", fetch_redirect_response=False)
        me_response = self.client.get("/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.wsgi_request.user.account.portal_subject, "portal-demo-admin")
        self.assertEqual(me_response.json()["user"]["roles"], ["asset-admin"])

    def test_switch_returns_to(self):
        response = self.client.post(
            "/auth/demo-switch",
            {"portal_subject": "portal-demo-employee", "returnTo": "/assets/"},
        )

        self.assertRedirects(response, "/assets/", fetch_redirect_response=False)

    @override_settings(AUTH_MODE="portal")
    def test_switch_blocked_in_portal_mode(self):
        response = self.client.post(
            "/auth/demo-switch",
            {"portal_subject": "portal-demo-employee", "returnTo": "/"},
        )

        self.assertEqual(response.status_code, 403)

    def test_switch_invalid_subject(self):
        response = self.client.post(
            "/auth/demo-switch",
            {"portal_subject": "portal-unknown", "returnTo": "/"},
        )

        self.assertEqual(response.status_code, 400)

    @override_settings(AUTH_MODE="dev-header", DEMO_SWITCH_SUBJECTS=["portal-nonexistent"])
    def test_switch_seed_not_loaded(self):
        response = self.client.post(
            "/auth/demo-switch",
            {"portal_subject": "portal-nonexistent", "returnTo": "/"},
        )

        self.assertEqual(response.status_code, 400)

    def test_context_processor_dev_mode(self):
        request = self.factory.get("/")
        request.account = self.demo_employee

        context = demo_context(request)

        self.assertEqual(context["auth_mode"], "dev-header")
        self.assertEqual([account.portal_subject for account in context["demo_accounts"]], [
            "portal-demo-employee",
            "portal-demo-admin",
        ])
        self.assertEqual(context["current_account"], self.demo_employee)

    @override_settings(AUTH_MODE="portal")
    def test_context_processor_portal_mode(self):
        request = self.factory.get("/")
        request.account = self.demo_employee

        context = demo_context(request)

        self.assertEqual(context["auth_mode"], "portal")
        self.assertEqual(context["demo_accounts"], [])
        self.assertEqual(context["current_account"], self.demo_employee)
