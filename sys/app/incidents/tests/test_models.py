from django.contrib.auth.models import User
from django.test import TestCase

from assets.models import Asset, AssetCategory
from incidents.models import IncidentReport
from incidents.services import IncidentError, report_incident, resolve_incident
from loans.models import LoanRecord, LoanRequest
from loans.services import LoanEligibilityError, check_loan_eligibility, confirm_return


class IncidentReportModelTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.asset = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            serial_number="SN-0001",
        )
        self.user = User.objects.create_user(username="reporter", password="password")

    def test_string_representation_includes_type_asset_and_status(self):
        report = IncidentReport.objects.create(
            asset=self.asset,
            incident_type=IncidentReport.TYPE_BREAKDOWN,
            reported_by=self.user,
        )

        self.assertIn("故障", str(report))
        self.assertIn("ASSET-001", str(report))
        self.assertIn("対応中", str(report))


class IncidentServiceTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.reporter = User.objects.create_user(username="reporter", password="password")
        self.resolver = User.objects.create_user(username="resolver", password="password")

    def create_asset(self, asset_code: str, status: str = Asset.STATUS_IN_STOCK) -> Asset:
        return Asset.objects.create(
            asset_code=asset_code,
            name=f"Asset {asset_code}",
            category=self.category,
            status=status,
            serial_number=f"SN-{asset_code}",
        )

    def test_report_incident_creates_record_and_updates_asset_status(self):
        for incident_type, asset_status in (
            (IncidentReport.TYPE_BREAKDOWN, Asset.STATUS_IN_REPAIR),
            (IncidentReport.TYPE_LOST, Asset.STATUS_LOST),
            (IncidentReport.TYPE_RETIRED, Asset.STATUS_RETIRED),
        ):
            with self.subTest(incident_type=incident_type):
                asset = self.create_asset(f"ASSET-{incident_type}")
                report = report_incident(
                    asset=asset,
                    incident_type=incident_type,
                    reporter=self.reporter,
                    description="demo",
                )

                asset.refresh_from_db()
                self.assertEqual(report.asset, asset)
                self.assertEqual(report.reported_by, self.reporter)
                self.assertEqual(asset.status, asset_status)

    def test_resolve_breakdown_restores_asset_to_in_stock(self):
        asset = self.create_asset("ASSET-BREAKDOWN")
        report = report_incident(
            asset=asset,
            incident_type=IncidentReport.TYPE_BREAKDOWN,
            reporter=self.reporter,
        )

        resolve_incident(report, resolver=self.resolver, resolution_notes="修理完了")

        report.refresh_from_db()
        asset.refresh_from_db()
        self.assertEqual(report.status, IncidentReport.STATUS_RESOLVED)
        self.assertEqual(report.resolved_by, self.resolver)
        self.assertEqual(asset.status, Asset.STATUS_IN_STOCK)

    def test_resolve_non_breakdown_raises_error(self):
        asset = self.create_asset("ASSET-LOST")
        report = report_incident(
            asset=asset,
            incident_type=IncidentReport.TYPE_LOST,
            reporter=self.reporter,
        )

        with self.assertRaises(IncidentError) as ctx:
            resolve_incident(report, resolver=self.resolver)

        self.assertIn("故障以外", str(ctx.exception))

    def test_report_on_retired_asset_raises_error(self):
        asset = self.create_asset("ASSET-RETIRED", status=Asset.STATUS_RETIRED)

        with self.assertRaises(IncidentError) as ctx:
            report_incident(
                asset=asset,
                incident_type=IncidentReport.TYPE_BREAKDOWN,
                reporter=self.reporter,
            )

        self.assertIn("廃棄済み", str(ctx.exception))

    def test_lost_asset_cannot_be_reported_lost_twice(self):
        asset = self.create_asset("ASSET-LOST", status=Asset.STATUS_LOST)

        with self.assertRaises(IncidentError) as ctx:
            report_incident(
                asset=asset,
                incident_type=IncidentReport.TYPE_LOST,
                reporter=self.reporter,
            )

        self.assertIn("紛失報告済み", str(ctx.exception))

    def test_loans_service_blocks_assets_with_incident_statuses(self):
        borrower = User.objects.create_user(username="borrower", password="password")
        for status in (Asset.STATUS_IN_REPAIR, Asset.STATUS_LOST, Asset.STATUS_RETIRED):
            with self.subTest(status=status):
                asset = self.create_asset(f"ASSET-{status}", status=status)
                with self.assertRaises(LoanEligibilityError):
                    check_loan_eligibility(asset, borrower)

    def test_return_confirmation_keeps_incident_status_when_asset_changed(self):
        borrower = User.objects.create_user(username="borrower2", password="password")
        asset = self.create_asset("ASSET-RETURN", status=Asset.STATUS_ON_LOAN)
        loan_request = LoanRequest.objects.create(
            asset=asset,
            requester=borrower,
            status=LoanRequest.STATUS_APPROVED,
            expected_start_date="2026-06-01",
        )
        loan_record = LoanRecord.objects.create(
            loan_request=loan_request,
            approved_by=self.resolver,
            loan_start_date="2026-06-01",
        )
        report_incident(
            asset=asset,
            incident_type=IncidentReport.TYPE_BREAKDOWN,
            reporter=self.reporter,
        )

        confirm_return(loan_record=loan_record, receiver=self.resolver)

        asset.refresh_from_db()
        self.assertEqual(asset.status, Asset.STATUS_IN_REPAIR)
