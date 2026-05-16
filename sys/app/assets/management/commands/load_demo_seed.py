import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Account, AppRole
from assets.models import Asset, AssetCategory
from incidents.models import IncidentReport
from incidents.services import report_incident
from inventory.models import InventoryResult, InventorySession
from inventory.services import close_inventory_session, open_inventory_session, record_inventory_result
from loans.models import LoanRecord, LoanRequest, ReturnRecord
from loans.services import approve_loan_request, confirm_return, create_loan_request, request_return


class Command(BaseCommand):
    help = "Load demo seed data for IT Asset Manager demo"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("カテゴリと資産の初期データを確認します。")
        categories = self.ensure_categories()
        assets = self.ensure_assets(categories)

        self.stdout.write("デモユーザーを確認します。")
        demo_employee = self.ensure_user(
            username="demo_employee",
            password="demo1234",
            display_name="Demo Employee",
            email="demo_employee@example.com",
            portal_subject="portal-demo-employee",
            role_codes=[],
            is_staff=False,
            is_superuser=False,
        )
        demo_admin = self.ensure_user(
            username="demo_admin",
            password="demo1234",
            display_name="Demo Admin",
            email="demo_admin@example.com",
            portal_subject="portal-demo-admin",
            role_codes=["asset-admin"],
            is_staff=True,
            is_superuser=True,
        )

        self.stdout.write("貸出履歴データを確認します。")
        self.ensure_active_loan(assets["LAPTOP-002"], demo_employee, demo_admin)
        self.ensure_returned_loan_history(assets["MON-001"], demo_employee, demo_admin)

        self.stdout.write("インシデントデータを確認します。")
        self.ensure_incident(assets["LAPTOP-003"], IncidentReport.TYPE_BREAKDOWN, demo_employee.user, "キーボード故障")
        self.ensure_incident(assets["PHONE-002"], IncidentReport.TYPE_LOST, demo_employee.user, "所在不明")
        self.ensure_incident(assets["MON-002"], IncidentReport.TYPE_RETIRED, demo_admin.user, "廃棄済み")

        self.stdout.write("棚卸しデータを確認します。")
        self.ensure_inventory_session(demo_admin.user, assets["LAPTOP-001"], assets["MON-001"])

        self.stdout.write(self.style.SUCCESS("デモシードデータの投入が完了しました。"))

    def ensure_categories(self) -> dict[str, AssetCategory]:
        definitions = [
            ("laptop", "ノートPC", 10),
            ("smartphone", "スマートフォン", 20),
            ("monitor", "モニター", 30),
        ]
        categories: dict[str, AssetCategory] = {}
        for code, name, sort_order in definitions:
            category, _ = AssetCategory.objects.update_or_create(
                code=code,
                defaults={"name": name, "sort_order": sort_order, "is_active": True},
            )
            categories[code] = category
        return categories

    def ensure_assets(self, categories: dict[str, AssetCategory]) -> dict[str, Asset]:
        definitions = [
            ("LAPTOP-001", "Lenovo ThinkPad X1", categories["laptop"], Asset.STATUS_IN_STOCK, "SN-LAPTOP-001", "Lenovo", "ThinkPad X1", "HQ-A1"),
            ("LAPTOP-002", "Dell Latitude 5440", categories["laptop"], Asset.STATUS_ON_LOAN, "SN-LAPTOP-002", "Dell", "Latitude 5440", "貸出中"),
            ("LAPTOP-003", "HP ProBook 440", categories["laptop"], Asset.STATUS_IN_REPAIR, "SN-LAPTOP-003", "HP", "ProBook 440", "修理受付"),
            ("LAPTOP-004", "MacBook Air 13", categories["laptop"], Asset.STATUS_IN_STOCK, "SN-LAPTOP-004", "Apple", "MacBook Air", "HQ-A2"),
            ("PHONE-001", "iPhone 14", categories["smartphone"], Asset.STATUS_IN_STOCK, "SN-PHONE-001", "Apple", "iPhone 14", "HQ-B1"),
            ("PHONE-002", "Pixel 8", categories["smartphone"], Asset.STATUS_LOST, "SN-PHONE-002", "Google", "Pixel 8", "所在不明"),
            ("MON-001", "Dell 27 Monitor", categories["monitor"], Asset.STATUS_IN_STOCK, "SN-MON-001", "Dell", "U2723QE", "会議室"),
            ("MON-002", "LG UltraFine", categories["monitor"], Asset.STATUS_RETIRED, "SN-MON-002", "LG", "27UP850", "廃棄済み"),
        ]
        assets: dict[str, Asset] = {}
        for asset_code, name, category, status, serial_number, manufacturer, model_name, location in definitions:
            asset, _ = Asset.objects.update_or_create(
                asset_code=asset_code,
                defaults={
                    "name": name,
                    "category": category,
                    "status": status,
                    "serial_number": serial_number,
                    "manufacturer": manufacturer,
                    "model_name": model_name,
                    "location": location,
                },
            )
            assets[asset_code] = asset
        return assets

    def ensure_user(
        self,
        *,
        username: str,
        password: str,
        display_name: str,
        email: str,
        portal_subject: str,
        role_codes: list[str],
        is_staff: bool,
        is_superuser: bool,
    ) -> Account:
        user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save(update_fields=["email", "password", "is_staff", "is_superuser"])

        account, _ = Account.objects.update_or_create(
            user=user,
            defaults={
                "portal_subject": portal_subject,
                "display_name": display_name,
                "email": email,
                "is_portal_active": True,
            },
        )

        roles = []
        for role_code in role_codes:
            role, _ = AppRole.objects.get_or_create(code=role_code, defaults={"name": role_code.title()})
            roles.append(role)
        account.roles.set(roles)
        return account

    def ensure_active_loan(self, asset: Asset, demo_employee: Account, demo_admin: Account) -> LoanRecord:
        loan_record = LoanRecord.objects.filter(
            loan_request__asset=asset,
            loan_request__requester=demo_employee.user,
            return_record__isnull=True,
        ).select_related("loan_request").first()
        if loan_record is not None:
            if asset.status != Asset.STATUS_ON_LOAN:
                asset.status = Asset.STATUS_ON_LOAN
                asset.save(update_fields=["status", "updated_at"])
            return loan_record

        asset.status = Asset.STATUS_IN_STOCK
        asset.save(update_fields=["status", "updated_at"])
        loan_request = create_loan_request(
            asset=asset,
            requester=demo_employee.user,
            expected_start_date=datetime.date.today() - datetime.timedelta(days=7),
            expected_return_date=datetime.date.today() + datetime.timedelta(days=7),
            purpose="営業持ち出しデモ",
        )
        return approve_loan_request(
            loan_request=loan_request,
            approver=demo_admin.user,
            loan_start_date=datetime.date.today() - datetime.timedelta(days=7),
            expected_return_date=datetime.date.today() + datetime.timedelta(days=7),
        )

    def ensure_returned_loan_history(self, asset: Asset, demo_employee: Account, demo_admin: Account) -> ReturnRecord:
        return_record = ReturnRecord.objects.filter(
            loan_record__loan_request__asset=asset,
            loan_record__loan_request__requester=demo_employee.user,
        ).select_related("loan_record").first()
        if return_record is not None:
            if asset.status != Asset.STATUS_IN_STOCK:
                asset.status = Asset.STATUS_IN_STOCK
                asset.save(update_fields=["status", "updated_at"])
            return return_record

        asset.status = Asset.STATUS_IN_STOCK
        asset.save(update_fields=["status", "updated_at"])
        loan_request = create_loan_request(
            asset=asset,
            requester=demo_employee.user,
            expected_start_date=datetime.date.today() - datetime.timedelta(days=30),
            expected_return_date=datetime.date.today() - datetime.timedelta(days=10),
            purpose="会議室利用デモ",
        )
        loan_record = approve_loan_request(
            loan_request=loan_request,
            approver=demo_admin.user,
            loan_start_date=datetime.date.today() - datetime.timedelta(days=30),
            expected_return_date=datetime.date.today() - datetime.timedelta(days=10),
        )
        request_return(loan_record=loan_record)
        return confirm_return(
            loan_record=loan_record,
            receiver=demo_admin.user,
            condition_notes="返却確認済み",
        )

    def ensure_incident(self, asset: Asset, incident_type: str, reporter: User, description: str) -> IncidentReport:
        report = IncidentReport.objects.filter(
            asset=asset,
            incident_type=incident_type,
            status=IncidentReport.STATUS_OPEN,
        ).first()
        if report is not None:
            status_map = {
                IncidentReport.TYPE_BREAKDOWN: Asset.STATUS_IN_REPAIR,
                IncidentReport.TYPE_LOST: Asset.STATUS_LOST,
                IncidentReport.TYPE_RETIRED: Asset.STATUS_RETIRED,
            }
            if asset.status != status_map[incident_type]:
                asset.status = status_map[incident_type]
                asset.save(update_fields=["status", "updated_at"])
            return report

        asset.status = Asset.STATUS_IN_STOCK
        asset.save(update_fields=["status", "updated_at"])
        return report_incident(
            asset=asset,
            incident_type=incident_type,
            reporter=reporter,
            description=description,
        )

    def ensure_inventory_session(self, admin_user: User, confirmed_asset: Asset, missing_asset: Asset) -> InventorySession:
        session = InventorySession.objects.filter(name="2026Q2 棚卸しデモ").first()
        if session is None:
            session = open_inventory_session(name="2026Q2 棚卸しデモ", created_by=admin_user, notes="デモ用サンプル")
        if session.status == InventorySession.STATUS_OPEN:
            record_inventory_result(
                session=session,
                asset=confirmed_asset,
                status=InventoryResult.STATUS_CONFIRMED,
                recorded_by=admin_user,
                notes="現物確認済み",
            )
            record_inventory_result(
                session=session,
                asset=missing_asset,
                status=InventoryResult.STATUS_MISSING,
                recorded_by=admin_user,
                notes="棚卸し時に未確認",
            )
            close_inventory_session(session=session, closed_by=admin_user)
        return session
