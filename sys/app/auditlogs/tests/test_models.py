from django.contrib.auth.models import User
from django.test import TestCase

from auditlogs.models import AuditLog
from auditlogs.services import log_action


class AuditLogServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auditor", password="password")

    def test_log_action_creates_record(self):
        log = log_action(
            AuditLog.ACTION_LOAN_REQUESTED,
            actor=self.user,
            asset_code="ASSET-001",
            object_repr="request-1",
        )

        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.asset_code, "ASSET-001")
        self.assertEqual(log.object_repr, "request-1")
        self.assertEqual(log.extra, {})

    def test_log_action_with_extra(self):
        log = log_action(
            AuditLog.ACTION_INVENTORY_RECORDED,
            actor=self.user,
            asset_code="ASSET-002",
            extra={"status": "missing", "session": "2026Q2"},
        )

        self.assertEqual(log.extra["status"], "missing")
        self.assertEqual(log.extra["session"], "2026Q2")
