from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import TestCase

from assets.models import Asset, AssetCategory


class AssetCategoryModelTests(TestCase):
    def test_category_string_representation_uses_name(self):
        category = AssetCategory.objects.create(code="laptop", name="Laptop")

        self.assertEqual(str(category), "Laptop")


class AssetModelTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(code="laptop", name="Laptop")

    def test_asset_is_available_for_loan_only_when_in_stock(self):
        asset = Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            status=Asset.STATUS_IN_STOCK,
            serial_number="SN-0001",
        )
        unavailable_asset = Asset.objects.create(
            asset_code="ASSET-002",
            name="ThinkPad X1 Yoga",
            category=self.category,
            status=Asset.STATUS_ON_LOAN,
            serial_number="SN-0002",
        )

        self.assertIs(asset.is_available_for_loan, True)
        self.assertIs(unavailable_asset.is_available_for_loan, False)

    def test_asset_code_must_be_unique(self):
        Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            serial_number="SN-0001",
        )
        duplicate = Asset(
            asset_code="ASSET-001",
            name="ThinkPad X1 Yoga",
            category=self.category,
            serial_number="SN-0002",
        )

        with self.assertRaises(ValidationError) as error:
            duplicate.full_clean()

        self.assertIn("asset_code", error.exception.message_dict)

    def test_serial_number_must_be_unique(self):
        Asset.objects.create(
            asset_code="ASSET-001",
            name="ThinkPad X1 Carbon",
            category=self.category,
            serial_number="SN-0001",
        )
        duplicate = Asset(
            asset_code="ASSET-002",
            name="ThinkPad X1 Yoga",
            category=self.category,
            serial_number="SN-0001",
        )

        with self.assertRaises(ValidationError) as error:
            duplicate.full_clean()

        self.assertIn("serial_number", error.exception.message_dict)

    def test_asset_and_category_are_registered_in_admin(self):
        self.assertTrue(admin.site.is_registered(Asset))
        self.assertTrue(admin.site.is_registered(AssetCategory))
