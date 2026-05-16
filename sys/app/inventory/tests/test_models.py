from django.contrib.auth.models import User
from django.test import TestCase

from assets.models import Asset, AssetCategory
from inventory.models import InventoryResult, InventorySession
from inventory.services import (
    InventoryError,
    close_inventory_session,
    get_discrepancies,
    open_inventory_session,
    record_inventory_result,
)


class InventorySessionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="creator", password="password")

    def test_string_representation_includes_name_and_status(self):
        session = InventorySession.objects.create(name="2026Q2", created_by=self.user)

        self.assertIn("2026Q2", str(session))
        self.assertIn("実施中", str(session))


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")
        self.user = User.objects.create_user(username="inventory-user", password="password")
        self.session = open_inventory_session("2026Q2 棚卸し", created_by=self.user, notes="demo")

    def create_asset(self, asset_code: str, status: str = Asset.STATUS_IN_STOCK) -> Asset:
        return Asset.objects.create(
            asset_code=asset_code,
            name=f"Asset {asset_code}",
            category=self.category,
            status=status,
            serial_number=f"SN-{asset_code}",
        )

    def test_open_inventory_session_creates_open_session(self):
        self.assertEqual(self.session.status, InventorySession.STATUS_OPEN)
        self.assertEqual(self.session.created_by, self.user)

    def test_record_inventory_result_creates_result_for_confirmed_and_missing(self):
        for status in (InventoryResult.STATUS_CONFIRMED, InventoryResult.STATUS_MISSING):
            with self.subTest(status=status):
                asset = self.create_asset(f"ASSET-{status}")
                result = record_inventory_result(
                    session=self.session,
                    asset=asset,
                    status=status,
                    recorded_by=self.user,
                    notes="checked",
                )
                self.assertEqual(result.status, status)
                self.assertEqual(result.recorded_by, self.user)

    def test_duplicate_record_updates_existing_result(self):
        asset = self.create_asset("ASSET-UPDATE")
        first = record_inventory_result(
            session=self.session,
            asset=asset,
            status=InventoryResult.STATUS_CONFIRMED,
            recorded_by=self.user,
        )
        second = record_inventory_result(
            session=self.session,
            asset=asset,
            status=InventoryResult.STATUS_MISSING,
            recorded_by=self.user,
            notes="not found",
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(InventoryResult.objects.count(), 1)
        self.assertEqual(second.status, InventoryResult.STATUS_MISSING)
        self.assertEqual(second.notes, "not found")

    def test_close_inventory_session_marks_session_closed(self):
        close_inventory_session(self.session, closed_by=self.user)

        self.session.refresh_from_db()
        self.assertEqual(self.session.status, InventorySession.STATUS_CLOSED)
        self.assertEqual(self.session.closed_by, self.user)
        self.assertIsNotNone(self.session.closed_at)

    def test_record_inventory_result_raises_for_closed_session(self):
        asset = self.create_asset("ASSET-CLOSED")
        close_inventory_session(self.session, closed_by=self.user)

        with self.assertRaises(InventoryError) as ctx:
            record_inventory_result(
                session=self.session,
                asset=asset,
                status=InventoryResult.STATUS_CONFIRMED,
                recorded_by=self.user,
            )

        self.assertIn("完了済み", str(ctx.exception))

    def test_get_discrepancies_returns_missing_in_stock_assets(self):
        in_stock_asset = self.create_asset("ASSET-MISSING")
        on_loan_asset = self.create_asset("ASSET-ONLOAN", status=Asset.STATUS_ON_LOAN)
        record_inventory_result(
            session=self.session,
            asset=in_stock_asset,
            status=InventoryResult.STATUS_MISSING,
            recorded_by=self.user,
        )
        record_inventory_result(
            session=self.session,
            asset=on_loan_asset,
            status=InventoryResult.STATUS_MISSING,
            recorded_by=self.user,
        )

        discrepancies = list(get_discrepancies(self.session))

        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0].asset, in_stock_asset)
