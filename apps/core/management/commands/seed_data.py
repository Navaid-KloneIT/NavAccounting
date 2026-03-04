"""
Master seeder command. Seeds all data for the NavAccounting application.

Usage:
    python manage.py seed_data              # Seed everything
    python manage.py seed_data --clean      # Wipe and re-seed
    python manage.py seed_data --tenants    # Seed tenants only
    python manage.py seed_data --users      # Seed users only
    python manage.py seed_data --company    # Seed company settings
    python manage.py seed_data --coa        # Seed chart of accounts
    python manage.py seed_data --dashboard  # Seed dashboard data
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.accounts.models import CustomUser, UserInvitation, UserProfile
from apps.company.models import (
    AccountType,
    ChartOfAccountsTemplate,
    ChartOfAccountsTemplateItem,
    CompanySettings,
    Currency,
    FiscalPeriod,
    FiscalYear,
)
from apps.dashboard.models import Alert, DashboardWidgetConfig
from apps.roles.models import Permission, Role, TenantUserRole
from apps.tenants.models import Tenant, TenantMembership

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with fake data for development'

    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true', help='Delete existing data first')
        parser.add_argument('--tenants', action='store_true', help='Seed tenants only')
        parser.add_argument('--users', action='store_true', help='Seed users only')
        parser.add_argument('--company', action='store_true', help='Seed company data only')
        parser.add_argument('--coa', action='store_true', help='Seed chart of accounts only')
        parser.add_argument('--dashboard', action='store_true', help='Seed dashboard data only')
        parser.add_argument('--gl', action='store_true', help='Seed general ledger data only')
        parser.add_argument('--ap', action='store_true', help='Seed accounts payable data only')
        parser.add_argument('--ar', action='store_true', help='Seed accounts receivable data only')

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Cleaning existing data...')
            self._clean()

        seed_all = not any([
            options['tenants'], options['users'], options['company'],
            options['coa'], options['dashboard'], options['gl'], options['ap'],
            options['ar'],
        ])

        # Always seed system-level data
        self.stdout.write('Seeding system data...')
        self._seed_currencies()
        self._seed_account_types()
        self._seed_permissions()

        if seed_all or options['coa']:
            self.stdout.write('Seeding COA templates...')
            self._seed_coa_templates()

        if seed_all or options['tenants']:
            self.stdout.write('Seeding tenants...')
            self._seed_tenants()

        if seed_all or options['users']:
            self.stdout.write('Seeding users...')
            self._seed_users()

        if seed_all or options['company']:
            self.stdout.write('Seeding company data...')
            self._seed_company_settings()

        if seed_all or options['dashboard']:
            self.stdout.write('Seeding dashboard data...')
            self._seed_dashboard_data()

        if seed_all or options['gl']:
            self.stdout.write('Seeding general ledger data...')
            self._seed_gl_data()

        if seed_all or options['ap']:
            self.stdout.write('Seeding accounts payable data...')
            self._seed_ap_data()

        if seed_all or options['ar']:
            self.stdout.write('Seeding accounts receivable data...')
            self._seed_ar_data()

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

    def _clean(self):
        # Clean AR data first (depends on GL and other models)
        try:
            from apps.accounts_receivable.models import (
                CustomerMessage, CustomerPortalToken, WriteOff,
                CollectionActivity, CreditMemo, ReceiptAllocation, Receipt,
                RecurringInvoiceTemplateLine, RecurringInvoiceTemplate,
                InvoiceApproval, InvoiceLine, Invoice, CustomerContact, Customer,
            )
            CustomerMessage.unscoped.all().delete()
            CustomerPortalToken.unscoped.all().delete()
            WriteOff.unscoped.all().delete()
            CollectionActivity.unscoped.all().delete()
            CreditMemo.unscoped.all().delete()
            ReceiptAllocation.objects.all().delete()
            Receipt.unscoped.all().delete()
            RecurringInvoiceTemplateLine.objects.all().delete()
            RecurringInvoiceTemplate.unscoped.all().delete()
            InvoiceApproval.unscoped.all().delete()
            InvoiceLine.objects.all().delete()
            Invoice.unscoped.all().delete()
            CustomerContact.objects.all().delete()
            Customer.unscoped.all().delete()
        except Exception:
            pass

        # Clean AP data (depends on GL and other models)
        try:
            from apps.accounts_payable.models import (
                VendorMessage, VendorPortalToken, ScheduledPayment,
                PaymentBatch, PaymentAllocation, Payment, BillUpload,
                BillApproval, BillLine, Bill, VendorContact, Vendor, PaymentTerm,
            )
            VendorMessage.unscoped.all().delete()
            VendorPortalToken.unscoped.all().delete()
            ScheduledPayment.unscoped.all().delete()
            PaymentBatch.unscoped.all().delete()
            PaymentAllocation.objects.all().delete()
            Payment.unscoped.all().delete()
            BillUpload.unscoped.all().delete()
            BillApproval.unscoped.all().delete()
            BillLine.objects.all().delete()
            Bill.unscoped.all().delete()
            VendorContact.objects.all().delete()
            Vendor.unscoped.all().delete()
            PaymentTerm.unscoped.all().delete()
        except Exception:
            pass

        # Clean GL data (depends on other models)
        try:
            from apps.general_ledger.models import (
                AuditTrail, AccountReconciliation, AllocationRuleLine, AllocationRule,
                PeriodCloseChecklist, JournalApproval, JournalEntryLine, JournalEntry,
                ExchangeRate, Account,
            )
            AuditTrail.unscoped.all().delete()
            AccountReconciliation.unscoped.all().delete()
            AllocationRuleLine.objects.all().delete()
            AllocationRule.unscoped.all().delete()
            PeriodCloseChecklist.unscoped.all().delete()
            JournalApproval.unscoped.all().delete()
            JournalEntryLine.objects.all().delete()
            JournalEntry.unscoped.all().delete()
            ExchangeRate.unscoped.all().delete()
            Account.unscoped.all().delete()
        except Exception:
            pass

        Alert.unscoped.all().delete()
        DashboardWidgetConfig.unscoped.all().delete()
        FiscalPeriod.unscoped.all().delete()
        FiscalYear.unscoped.all().delete()
        CompanySettings.unscoped.all().delete()
        TenantUserRole.unscoped.all().delete()
        Role.unscoped.all().delete()
        UserInvitation.unscoped.all().delete()
        UserProfile.unscoped.all().delete()
        TenantMembership.objects.all().delete()
        Tenant.objects.all().delete()
        CustomUser.objects.filter(is_superuser=False).delete()
        ChartOfAccountsTemplateItem.objects.all().delete()
        ChartOfAccountsTemplate.objects.all().delete()
        Permission.objects.all().delete()
        AccountType.objects.all().delete()
        Currency.objects.all().delete()

    def _seed_currencies(self):
        currencies = [
            ('USD', 'US Dollar', '$', 2),
            ('EUR', 'Euro', '\u20ac', 2),
            ('GBP', 'British Pound', '\u00a3', 2),
            ('JPY', 'Japanese Yen', '\u00a5', 0),
            ('CAD', 'Canadian Dollar', 'C$', 2),
            ('AUD', 'Australian Dollar', 'A$', 2),
            ('CHF', 'Swiss Franc', 'CHF', 2),
            ('CNY', 'Chinese Yuan', '\u00a5', 2),
            ('INR', 'Indian Rupee', '\u20b9', 2),
            ('BRL', 'Brazilian Real', 'R$', 2),
            ('MXN', 'Mexican Peso', 'Mex$', 2),
            ('SGD', 'Singapore Dollar', 'S$', 2),
            ('HKD', 'Hong Kong Dollar', 'HK$', 2),
            ('KRW', 'South Korean Won', '\u20a9', 0),
            ('SEK', 'Swedish Krona', 'kr', 2),
            ('NOK', 'Norwegian Krone', 'kr', 2),
            ('DKK', 'Danish Krone', 'kr', 2),
            ('ZAR', 'South African Rand', 'R', 2),
            ('AED', 'UAE Dirham', '\u062f.\u0625', 2),
            ('SAR', 'Saudi Riyal', '\ufdfc', 2),
            ('NZD', 'New Zealand Dollar', 'NZ$', 2),
            ('THB', 'Thai Baht', '\u0e3f', 2),
            ('PHP', 'Philippine Peso', '\u20b1', 2),
            ('IDR', 'Indonesian Rupiah', 'Rp', 0),
            ('MYR', 'Malaysian Ringgit', 'RM', 2),
            ('TWD', 'Taiwan Dollar', 'NT$', 0),
            ('PLN', 'Polish Zloty', 'z\u0142', 2),
            ('TRY', 'Turkish Lira', '\u20ba', 2),
            ('RUB', 'Russian Ruble', '\u20bd', 2),
            ('EGP', 'Egyptian Pound', 'E\u00a3', 2),
        ]
        for code, name, symbol, decimals in currencies:
            Currency.objects.get_or_create(
                code=code,
                defaults={'name': name, 'symbol': symbol, 'decimal_places': decimals}
            )
        self.stdout.write(f'  Created {len(currencies)} currencies')

    def _seed_account_types(self):
        types = [
            ('ASSET', 'Assets', 'debit', 1),
            ('LIABILITY', 'Liabilities', 'credit', 2),
            ('EQUITY', 'Equity', 'credit', 3),
            ('REVENUE', 'Revenue', 'credit', 4),
            ('EXPENSE', 'Expenses', 'debit', 5),
        ]
        for code, name, balance, order in types:
            AccountType.objects.get_or_create(
                code=code,
                defaults={'name': name, 'normal_balance': balance, 'display_order': order}
            )
        self.stdout.write(f'  Created {len(types)} account types')

    def _seed_permissions(self):
        perms = [
            ('view_dashboard', 'View Dashboard', 'dashboard'),
            ('manage_widgets', 'Manage Dashboard Widgets', 'dashboard'),
            ('view_reports', 'View Reports', 'dashboard'),
            ('view_users', 'View Users', 'user_management'),
            ('invite_users', 'Invite Users', 'user_management'),
            ('manage_users', 'Manage Users', 'user_management'),
            ('manage_roles', 'Manage Roles', 'user_management'),
            ('view_company', 'View Company Settings', 'company'),
            ('manage_company', 'Manage Company Settings', 'company'),
            ('manage_fiscal_years', 'Manage Fiscal Years', 'company'),
            ('view_coa', 'View Chart of Accounts', 'company'),
            ('manage_coa', 'Manage Chart of Accounts', 'company'),
            ('view_journal', 'View Journal Entries', 'general_ledger'),
            ('create_journal', 'Create Journal Entries', 'general_ledger'),
            ('approve_journal', 'Approve Journal Entries', 'general_ledger'),
            ('post_journal', 'Post Journal Entries', 'general_ledger'),
            ('manage_coa_accounts', 'Manage Chart of Accounts (GL)', 'general_ledger'),
            ('manage_periods', 'Manage Period Close', 'general_ledger'),
            ('reconcile_accounts', 'Reconcile Accounts', 'general_ledger'),
            ('manage_allocations', 'Manage Allocation Rules', 'general_ledger'),
            ('run_allocations', 'Run Allocations', 'general_ledger'),
            ('view_audit_trail', 'View Audit Trail', 'general_ledger'),
            ('manage_exchange_rates', 'Manage Exchange Rates', 'general_ledger'),
            ('view_ap', 'View Accounts Payable', 'accounts_payable'),
            ('manage_ap', 'Manage Accounts Payable', 'accounts_payable'),
            ('create_bill', 'Create Bills', 'accounts_payable'),
            ('approve_bill', 'Approve Bills', 'accounts_payable'),
            ('create_payment', 'Create Payments', 'accounts_payable'),
            ('void_payment', 'Void Payments', 'accounts_payable'),
            ('manage_vendors', 'Manage Vendors', 'accounts_payable'),
            ('view_ap_reports', 'View AP Reports', 'accounts_payable'),
            ('manage_vendor_portal', 'Manage Vendor Portal', 'accounts_payable'),
            ('view_ar', 'View Accounts Receivable', 'accounts_receivable'),
            ('manage_ar', 'Manage Accounts Receivable', 'accounts_receivable'),
            ('create_invoice', 'Create Invoices', 'accounts_receivable'),
            ('approve_invoice', 'Approve Invoices', 'accounts_receivable'),
            ('send_invoice', 'Send Invoices', 'accounts_receivable'),
            ('create_receipt', 'Create Receipts', 'accounts_receivable'),
            ('void_receipt', 'Void Receipts', 'accounts_receivable'),
            ('manage_customers', 'Manage Customers', 'accounts_receivable'),
            ('view_ar_reports', 'View AR Reports', 'accounts_receivable'),
            ('manage_collections', 'Manage Collections', 'accounts_receivable'),
            ('approve_write_off', 'Approve Write-Offs', 'accounts_receivable'),
            ('manage_credit', 'Manage Credit Limits', 'accounts_receivable'),
            ('manage_recurring', 'Manage Recurring Invoices', 'accounts_receivable'),
            ('manage_customer_portal', 'Manage Customer Portal', 'accounts_receivable'),
            ('view_bank', 'View Bank Accounts', 'cash_management'),
            ('manage_bank', 'Manage Bank Accounts', 'cash_management'),
            ('reconcile_bank', 'Reconcile Bank Accounts', 'cash_management'),
            ('view_assets', 'View Fixed Assets', 'fixed_assets'),
            ('manage_assets', 'Manage Fixed Assets', 'fixed_assets'),
            ('admin_full', 'Full Administration Access', 'system'),
        ]
        for codename, name, module in perms:
            Permission.objects.get_or_create(
                codename=codename,
                defaults={'name': name, 'module': module}
            )
        self.stdout.write(f'  Created {len(perms)} permissions')

    def _seed_coa_templates(self):
        asset_type = AccountType.objects.get(code='ASSET')
        liability_type = AccountType.objects.get(code='LIABILITY')
        equity_type = AccountType.objects.get(code='EQUITY')
        revenue_type = AccountType.objects.get(code='REVENUE')
        expense_type = AccountType.objects.get(code='EXPENSE')

        # Standard Business Template
        template, _ = ChartOfAccountsTemplate.objects.get_or_create(
            name='Standard Business',
            defaults={
                'description': 'Comprehensive chart of accounts for standard businesses.',
                'country': 'United States',
                'is_default': True,
            }
        )

        accounts = [
            # Assets
            ('1000', 'Assets', asset_type, True, None, 1),
            ('1100', 'Cash and Cash Equivalents', asset_type, True, '1000', 2),
            ('1110', 'Checking Account', asset_type, False, '1100', 3),
            ('1120', 'Savings Account', asset_type, False, '1100', 4),
            ('1130', 'Petty Cash', asset_type, False, '1100', 5),
            ('1200', 'Accounts Receivable', asset_type, True, '1000', 6),
            ('1210', 'Trade Receivables', asset_type, False, '1200', 7),
            ('1220', 'Other Receivables', asset_type, False, '1200', 8),
            ('1230', 'Allowance for Doubtful Accounts', asset_type, False, '1200', 9),
            ('1300', 'Inventory', asset_type, True, '1000', 10),
            ('1310', 'Finished Goods', asset_type, False, '1300', 11),
            ('1320', 'Raw Materials', asset_type, False, '1300', 12),
            ('1400', 'Prepaid Expenses', asset_type, False, '1000', 13),
            ('1500', 'Fixed Assets', asset_type, True, '1000', 14),
            ('1510', 'Land', asset_type, False, '1500', 15),
            ('1520', 'Buildings', asset_type, False, '1500', 16),
            ('1530', 'Equipment', asset_type, False, '1500', 17),
            ('1540', 'Vehicles', asset_type, False, '1500', 18),
            ('1550', 'Furniture & Fixtures', asset_type, False, '1500', 19),
            ('1560', 'Accumulated Depreciation', asset_type, False, '1500', 20),
            # Liabilities
            ('2000', 'Liabilities', liability_type, True, None, 21),
            ('2100', 'Current Liabilities', liability_type, True, '2000', 22),
            ('2110', 'Accounts Payable', liability_type, False, '2100', 23),
            ('2120', 'Accrued Expenses', liability_type, False, '2100', 24),
            ('2130', 'Salaries Payable', liability_type, False, '2100', 25),
            ('2140', 'Taxes Payable', liability_type, False, '2100', 26),
            ('2150', 'Unearned Revenue', liability_type, False, '2100', 27),
            ('2200', 'Long-term Liabilities', liability_type, True, '2000', 28),
            ('2210', 'Bank Loans', liability_type, False, '2200', 29),
            ('2220', 'Mortgage Payable', liability_type, False, '2200', 30),
            # Equity
            ('3000', 'Equity', equity_type, True, None, 31),
            ('3100', 'Common Stock', equity_type, False, '3000', 32),
            ('3200', 'Retained Earnings', equity_type, False, '3000', 33),
            ('3300', 'Owner\'s Equity', equity_type, False, '3000', 34),
            ('3400', 'Dividends', equity_type, False, '3000', 35),
            # Revenue
            ('4000', 'Revenue', revenue_type, True, None, 36),
            ('4100', 'Sales Revenue', revenue_type, False, '4000', 37),
            ('4200', 'Service Revenue', revenue_type, False, '4000', 38),
            ('4300', 'Interest Income', revenue_type, False, '4000', 39),
            ('4400', 'Other Income', revenue_type, False, '4000', 40),
            ('4500', 'Sales Returns & Allowances', revenue_type, False, '4000', 41),
            ('4600', 'Sales Discounts', revenue_type, False, '4000', 42),
            # Expenses
            ('5000', 'Cost of Goods Sold', expense_type, True, None, 43),
            ('5100', 'Cost of Goods Sold', expense_type, False, '5000', 44),
            ('5200', 'Direct Labor', expense_type, False, '5000', 45),
            ('5300', 'Manufacturing Overhead', expense_type, False, '5000', 46),
            ('6000', 'Operating Expenses', expense_type, True, None, 47),
            ('6100', 'Salaries & Wages', expense_type, False, '6000', 48),
            ('6200', 'Rent Expense', expense_type, False, '6000', 49),
            ('6300', 'Utilities Expense', expense_type, False, '6000', 50),
            ('6400', 'Insurance Expense', expense_type, False, '6000', 51),
            ('6500', 'Depreciation Expense', expense_type, False, '6000', 52),
            ('6600', 'Office Supplies', expense_type, False, '6000', 53),
            ('6700', 'Marketing & Advertising', expense_type, False, '6000', 54),
            ('6800', 'Professional Services', expense_type, False, '6000', 55),
            ('6900', 'Travel & Entertainment', expense_type, False, '6000', 56),
            ('7000', 'Technology & Software', expense_type, False, '6000', 57),
            ('7100', 'Telephone & Internet', expense_type, False, '6000', 58),
            ('7200', 'Bank Fees & Charges', expense_type, False, '6000', 59),
            ('7300', 'Interest Expense', expense_type, False, None, 60),
            ('7400', 'Tax Expense', expense_type, False, None, 61),
        ]

        parent_map = {}
        for code, name, acc_type, is_header, parent_code, order in accounts:
            parent = parent_map.get(parent_code) if parent_code else None
            item, _ = ChartOfAccountsTemplateItem.objects.get_or_create(
                template=template,
                account_code=code,
                defaults={
                    'account_name': name,
                    'account_type': acc_type,
                    'parent': parent,
                    'is_header': is_header,
                    'display_order': order,
                }
            )
            parent_map[code] = item

        self.stdout.write(f'  Created COA template with {len(accounts)} accounts')

    def _seed_tenants(self):
        # Create superuser first
        superuser, created = CustomUser.objects.get_or_create(
            email='admin@navaccounting.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True,
            }
        )
        if created:
            superuser.set_password('admin123!')
            superuser.save()
            self.stdout.write('  Created superuser: admin@navaccounting.com / admin123!')

        tenants_data = [
            ('Acme Corporation', 'acme-corp'),
            ('TechStart Solutions', 'techstart'),
            ('Green Valley Farms', 'green-valley'),
        ]

        for name, slug in tenants_data:
            tenant, _ = Tenant.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'owner': superuser}
            )
            TenantMembership.objects.get_or_create(
                user=superuser,
                tenant=tenant,
                defaults={'is_default': slug == 'acme-corp'}
            )

        self.stdout.write(f'  Created {len(tenants_data)} tenants')

    def _seed_users(self):
        tenants = Tenant.objects.all()
        all_perms = Permission.objects.all()

        for tenant in tenants:
            # Create system roles
            admin_role, _ = Role.unscoped.get_or_create(
                name='Admin',
                tenant=tenant,
                defaults={'description': 'Full access to all features', 'is_system_role': True}
            )
            admin_role.permissions.set(all_perms)

            manager_perms = all_perms.exclude(codename='admin_full')
            manager_role, _ = Role.unscoped.get_or_create(
                name='Manager',
                tenant=tenant,
                defaults={'description': 'Manage operations and approve transactions', 'is_system_role': True}
            )
            manager_role.permissions.set(manager_perms)

            view_perms = all_perms.filter(codename__startswith='view_')
            accountant_role, _ = Role.unscoped.get_or_create(
                name='Accountant',
                tenant=tenant,
                defaults={'description': 'Record and manage financial transactions', 'is_system_role': True}
            )
            accountant_role.permissions.set(
                all_perms.filter(module__in=['general_ledger', 'accounts_payable', 'accounts_receivable', 'dashboard'])
            )

            viewer_role, _ = Role.unscoped.get_or_create(
                name='Viewer',
                tenant=tenant,
                defaults={'description': 'Read-only access to reports and dashboards', 'is_system_role': True}
            )
            viewer_role.permissions.set(view_perms)

            # Assign admin role to superuser
            superuser = CustomUser.objects.get(email='admin@navaccounting.com')
            TenantUserRole.unscoped.get_or_create(
                user=superuser, role=admin_role, tenant=tenant,
                defaults={'assigned_by': superuser}
            )

            # Create users for each role
            roles_users = [
                (manager_role, 2),
                (accountant_role, 5),
                (viewer_role, 3),
            ]

            for role, count in roles_users:
                for i in range(count):
                    first_name = fake.first_name()
                    last_name = fake.last_name()
                    email = f"{first_name.lower()}.{last_name.lower()}@{tenant.slug}.example.com"
                    username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 99)}"

                    user, created = CustomUser.objects.get_or_create(
                        email=email,
                        defaults={
                            'username': username,
                            'first_name': first_name,
                            'last_name': last_name,
                            'phone': fake.phone_number()[:20],
                            'is_email_verified': True,
                        }
                    )
                    if created:
                        user.set_password('password123!')
                        user.save()

                    membership, _ = TenantMembership.objects.get_or_create(
                        user=user, tenant=tenant
                    )
                    TenantUserRole.unscoped.get_or_create(
                        user=user, role=role, tenant=tenant,
                        defaults={'assigned_by': superuser}
                    )

                    # Create profile
                    UserProfile.unscoped.get_or_create(
                        user=user, tenant=tenant,
                        defaults={
                            'job_title': fake.job()[:100],
                            'department': random.choice([
                                'Finance', 'Accounting', 'Operations',
                                'Management', 'Sales', 'IT'
                            ]),
                            'bio': fake.text(max_nb_chars=200),
                        }
                    )

        self.stdout.write(f'  Created users and roles for {tenants.count()} tenants')

    def _seed_company_settings(self):
        usd = Currency.objects.get(code='USD')

        for tenant in Tenant.objects.all():
            settings, _ = CompanySettings.unscoped.get_or_create(
                tenant=tenant,
                defaults={
                    'company_name': tenant.name,
                    'legal_name': f'{tenant.name} LLC',
                    'tax_id': fake.ssn(),
                    'registration_number': f'REG-{fake.random_number(digits=8)}',
                    'address_line_1': fake.street_address(),
                    'city': fake.city(),
                    'state': fake.state_abbr(),
                    'postal_code': fake.zipcode(),
                    'country': 'United States',
                    'base_currency': usd,
                    'phone': fake.phone_number()[:20],
                    'email': f'info@{tenant.slug}.example.com',
                    'website': f'https://www.{tenant.slug}.example.com',
                }
            )

            # Create fiscal year
            fy, _ = FiscalYear.unscoped.get_or_create(
                name='FY 2025-2026',
                tenant=tenant,
                defaults={
                    'start_date': date(2025, 1, 1),
                    'end_date': date(2025, 12, 31),
                    'is_current': True,
                }
            )

            # Create fiscal periods
            for month in range(1, 13):
                start = date(2025, month, 1)
                if month == 12:
                    end = date(2025, 12, 31)
                else:
                    end = date(2025, month + 1, 1) - timedelta(days=1)

                FiscalPeriod.unscoped.get_or_create(
                    fiscal_year=fy,
                    period_number=month,
                    tenant=tenant,
                    defaults={
                        'name': start.strftime('%B %Y'),
                        'start_date': start,
                        'end_date': end,
                    }
                )

        self.stdout.write('  Created company settings and fiscal years')

    def _seed_dashboard_data(self):
        alert_templates = [
            ('Overdue Invoice #INV-1042', 'Invoice for $3,500 is 15 days overdue.', 'danger', 'overdue_payment'),
            ('Overdue Invoice #INV-1038', 'Invoice for $1,200 is 8 days overdue.', 'warning', 'overdue_payment'),
            ('Low Cash Balance Alert', 'Checking account balance below $10,000 threshold.', 'danger', 'low_balance'),
            ('Payment Received', 'Payment of $5,000 received from Client ABC.', 'success', 'payment_received'),
            ('Bank Reconciliation Due', 'Monthly bank reconciliation is pending.', 'warning', 'reconciliation'),
            ('New User Joined', 'John Smith has accepted the invitation.', 'info', 'user_activity'),
            ('Fiscal Year End Approaching', '45 days until fiscal year end. Start year-end close.', 'warning', 'fiscal_year'),
            ('Expense Anomaly Detected', 'Travel expenses 40% above monthly average.', 'warning', 'anomaly'),
            ('Budget Alert', 'Marketing budget is 90% utilized.', 'warning', 'budget'),
            ('System Update', 'New features available. Check release notes.', 'info', 'system'),
            ('Tax Filing Reminder', 'Quarterly tax filing due in 10 days.', 'danger', 'tax'),
            ('Vendor Payment Due', '3 vendor payments due this week totaling $12,500.', 'warning', 'payment_due'),
        ]

        for tenant in Tenant.objects.all():
            for title, message, severity, alert_type in alert_templates:
                Alert.unscoped.get_or_create(
                    title=title,
                    tenant=tenant,
                    defaults={
                        'message': message,
                        'severity': severity,
                        'alert_type': alert_type,
                    }
                )

            # Create widget configs for the admin user
            superuser = CustomUser.objects.get(email='admin@navaccounting.com')
            widgets = [
                ('kpi_cards', 0, 12),
                ('cash_flow', 1, 8),
                ('alert_center', 2, 4),
                ('quick_actions', 3, 4),
                ('executive_summary', 4, 8),
            ]
            for widget_type, position, col_span in widgets:
                DashboardWidgetConfig.unscoped.get_or_create(
                    user=superuser,
                    tenant=tenant,
                    widget_type=widget_type,
                    defaults={'position': position, 'column_span': col_span}
                )

        self.stdout.write('  Created dashboard alerts and widget configs')

    def _seed_gl_data(self):
        """Seed general ledger data: import COA template, exchange rates, sample journal entries."""
        from apps.general_ledger.models import Account, JournalEntry, JournalEntryLine, ExchangeRate

        template = ChartOfAccountsTemplate.objects.filter(is_default=True).first()
        if not template:
            self.stdout.write('  No default COA template found, skipping GL seed.')
            return

        for tenant in Tenant.objects.all():
            # Import accounts from default template
            items = template.items.select_related('account_type', 'parent').order_by('display_order')
            parent_map = {}
            created_count = 0
            for item in items:
                parent = parent_map.get(item.parent_id) if item.parent_id else None
                account, created = Account.unscoped.get_or_create(
                    tenant=tenant,
                    account_number=item.account_code,
                    defaults={
                        'name': item.account_name,
                        'account_type': item.account_type,
                        'parent': parent,
                        'is_header': item.is_header,
                        'description': item.description,
                        'display_order': item.display_order,
                    }
                )
                parent_map[item.pk] = account
                if created:
                    created_count += 1

            # Seed exchange rates
            usd = Currency.objects.filter(code='USD').first()
            eur = Currency.objects.filter(code='EUR').first()
            gbp = Currency.objects.filter(code='GBP').first()
            if usd and eur and gbp:
                for from_c, to_c, rate in [(usd, eur, '0.92000000'), (usd, gbp, '0.79000000'), (eur, gbp, '0.86000000')]:
                    ExchangeRate.unscoped.get_or_create(
                        tenant=tenant,
                        from_currency=from_c,
                        to_currency=to_c,
                        effective_date=date(2025, 1, 1),
                        defaults={'rate': Decimal(rate), 'source': 'seed'}
                    )

            # Seed sample journal entries
            fy = FiscalYear.unscoped.filter(tenant=tenant, is_current=True).first()
            if not fy:
                continue
            period = FiscalPeriod.unscoped.filter(fiscal_year=fy, tenant=tenant, period_number=1).first()
            if not period:
                continue

            superuser = CustomUser.objects.filter(email='admin@navaccounting.com').first()
            if not superuser or not usd:
                continue

            sample_entries = [
                {
                    'description': 'Initial Capital Investment',
                    'date': date(2025, 1, 5),
                    'lines': [('1110', Decimal('50000.00'), Decimal('0.00')), ('3300', Decimal('0.00'), Decimal('50000.00'))]
                },
                {
                    'description': 'Office Rent Payment',
                    'date': date(2025, 1, 10),
                    'lines': [('6200', Decimal('2500.00'), Decimal('0.00')), ('1110', Decimal('0.00'), Decimal('2500.00'))]
                },
                {
                    'description': 'Service Revenue from Client',
                    'date': date(2025, 1, 15),
                    'lines': [('1210', Decimal('15000.00'), Decimal('0.00')), ('4200', Decimal('0.00'), Decimal('15000.00'))]
                },
            ]

            for i, entry_data in enumerate(sample_entries, start=1):
                entry_number = f"JE-2025-{i:04d}"
                je, created = JournalEntry.unscoped.get_or_create(
                    tenant=tenant,
                    entry_number=entry_number,
                    defaults={
                        'date': entry_data['date'],
                        'description': entry_data['description'],
                        'fiscal_period': period,
                        'status': 'posted',
                        'source': 'system',
                        'currency': usd,
                        'created_by': superuser,
                        'posted_by': superuser,
                        'posted_at': timezone.now(),
                    }
                )
                if created:
                    for acc_code, debit, credit in entry_data['lines']:
                        account = Account.unscoped.filter(tenant=tenant, account_number=acc_code).first()
                        if account:
                            JournalEntryLine.objects.create(
                                journal_entry=je,
                                account=account,
                                debit=debit,
                                credit=credit,
                            )

        self.stdout.write(f'  Created GL data (accounts, exchange rates, journal entries)')

    def _seed_ap_data(self):
        """Seed accounts payable data: payment terms, vendors, bills, payments,
        batches, uploads, scheduled payments."""
        from apps.accounts_payable.models import (
            PaymentTerm, Vendor, VendorContact, Bill, BillLine, Payment,
            PaymentAllocation, PaymentBatch, BillUpload, ScheduledPayment,
            VendorPortalToken,
        )
        from apps.general_ledger.models import Account

        superuser = CustomUser.objects.filter(email='admin@navaccounting.com').first()
        if not superuser:
            self.stdout.write('  No superuser found, skipping AP seed.')
            return

        usd = Currency.objects.filter(code='USD').first()

        for tenant in Tenant.objects.all():
            # --- Payment Terms ---
            terms_data = [
                ('Net 15', 'NET15', 15, Decimal('0.00'), 0),
                ('Net 30', 'NET30', 30, Decimal('0.00'), 0),
                ('Net 45', 'NET45', 45, Decimal('0.00'), 0),
                ('Net 60', 'NET60', 60, Decimal('0.00'), 0),
                ('2/10 Net 30', '2/10N30', 30, Decimal('2.00'), 10),
                ('1/10 Net 45', '1/10N45', 45, Decimal('1.00'), 10),
                ('Due on Receipt', 'DOR', 0, Decimal('0.00'), 0),
            ]

            term_map = {}
            for name, code, due_days, disc_pct, disc_days in terms_data:
                term, _ = PaymentTerm.unscoped.get_or_create(
                    tenant=tenant,
                    code=code,
                    defaults={
                        'name': name,
                        'due_days': due_days,
                        'discount_percentage': disc_pct,
                        'discount_days': disc_days,
                    }
                )
                term_map[code] = term

            # Lookup GL accounts
            ap_account = Account.unscoped.filter(
                tenant=tenant, account_number='2110'
            ).first()
            checking = Account.unscoped.filter(
                tenant=tenant, account_number='1110'
            ).first()
            office_supplies = Account.unscoped.filter(
                tenant=tenant, account_number='6600'
            ).first()
            rent_expense = Account.unscoped.filter(
                tenant=tenant, account_number='6200'
            ).first()
            utilities_expense = Account.unscoped.filter(
                tenant=tenant, account_number='6300'
            ).first()
            prof_services = Account.unscoped.filter(
                tenant=tenant, account_number='6800'
            ).first()
            tech_software = Account.unscoped.filter(
                tenant=tenant, account_number='7000'
            ).first()

            if not ap_account or not checking:
                self.stdout.write(f'  Skipping {tenant.name}: missing AP or checking account')
                continue

            fy = FiscalYear.unscoped.filter(tenant=tenant, is_current=True).first()
            period = FiscalPeriod.unscoped.filter(
                fiscal_year=fy, tenant=tenant, period_number=1
            ).first() if fy else None

            # --- Vendors ---
            vendors_data = [
                {
                    'company_name': 'Staples Office Supply',
                    'display_name': 'Staples',
                    'vendor_type': 'supplier',
                    'tax_id': '12-3456789',
                    'is_1099_eligible': False,
                    'payment_term': 'NET30',
                    'expense_account': office_supplies,
                    'payment_method': 'ach',
                    'contacts': [
                        ('Sarah', 'Johnson', 'Account Manager', 'sarah.j@staples.example.com', '555-0101', True),
                    ],
                },
                {
                    'company_name': 'City Property Management LLC',
                    'display_name': 'City Property Mgmt',
                    'vendor_type': 'supplier',
                    'tax_id': '98-7654321',
                    'is_1099_eligible': True,
                    'payment_term': 'NET15',
                    'expense_account': rent_expense,
                    'payment_method': 'check',
                    'contacts': [
                        ('Mike', 'Chen', 'Property Manager', 'mike@cityprop.example.com', '555-0201', True),
                    ],
                },
                {
                    'company_name': 'Pacific Gas & Electric',
                    'display_name': 'PG&E',
                    'vendor_type': 'utility',
                    'tax_id': '55-1234567',
                    'is_1099_eligible': False,
                    'payment_term': 'NET15',
                    'expense_account': utilities_expense,
                    'payment_method': 'ach',
                    'contacts': [
                        ('Lisa', 'Wong', 'Billing', 'billing@pge.example.com', '555-0301', True),
                    ],
                },
                {
                    'company_name': 'Anderson & Associates CPA',
                    'display_name': 'Anderson CPA',
                    'vendor_type': 'contractor',
                    'tax_id': '33-9876543',
                    'is_1099_eligible': True,
                    'payment_term': '2/10N30',
                    'expense_account': prof_services,
                    'payment_method': 'check',
                    'contacts': [
                        ('James', 'Anderson', 'Partner', 'james@andersoncpa.example.com', '555-0401', True),
                        ('Emily', 'Park', 'Staff Accountant', 'emily@andersoncpa.example.com', '555-0402', False),
                    ],
                },
                {
                    'company_name': 'CloudTech Solutions Inc',
                    'display_name': 'CloudTech',
                    'vendor_type': 'supplier',
                    'tax_id': '77-5555555',
                    'is_1099_eligible': False,
                    'payment_term': 'NET30',
                    'expense_account': tech_software,
                    'payment_method': 'ach',
                    'contacts': [
                        ('David', 'Kim', 'Sales Rep', 'david@cloudtech.example.com', '555-0501', True),
                    ],
                },
            ]

            vendor_objs = []
            for i, vdata in enumerate(vendors_data, start=1):
                vendor_number = f"VND-{i:04d}"
                vendor, created = Vendor.unscoped.get_or_create(
                    tenant=tenant,
                    vendor_number=vendor_number,
                    defaults={
                        'company_name': vdata['company_name'],
                        'display_name': vdata['display_name'],
                        'vendor_type': vdata['vendor_type'],
                        'tax_id': vdata['tax_id'],
                        'is_1099_eligible': vdata['is_1099_eligible'],
                        'address_line_1': fake.street_address(),
                        'city': fake.city(),
                        'state': fake.state_abbr(),
                        'postal_code': fake.zipcode(),
                        'country': 'US',
                        'default_payment_term': term_map.get(vdata['payment_term']),
                        'default_expense_account': vdata['expense_account'],
                        'currency': usd,
                        'preferred_payment_method': vdata['payment_method'],
                    }
                )
                vendor_objs.append(vendor)

                if created:
                    for first, last, title, email, phone, is_primary in vdata['contacts']:
                        VendorContact.objects.get_or_create(
                            vendor=vendor,
                            email=email,
                            defaults={
                                'first_name': first,
                                'last_name': last,
                                'title': title,
                                'phone': phone,
                                'is_primary': is_primary,
                            }
                        )

                    # Create portal token for first vendor
                    if i == 1:
                        VendorPortalToken.unscoped.get_or_create(
                            tenant=tenant,
                            vendor=vendor,
                            defaults={
                                'is_active': True,
                                'expires_at': timezone.now() + timedelta(days=365),
                            }
                        )

            # --- Bills ---
            if not period:
                continue

            bills_data = [
                {
                    'vendor': vendor_objs[0],  # Staples
                    'invoice_number': 'INV-ST-20250105',
                    'bill_date': date(2025, 1, 5),
                    'description': 'Office supplies - January',
                    'status': 'approved',
                    'lines': [
                        (office_supplies, 'Printer paper (10 reams)', 10, Decimal('24.99'), Decimal('249.90')),
                        (office_supplies, 'Ink cartridges', 4, Decimal('35.00'), Decimal('140.00')),
                        (office_supplies, 'Pens and markers', 1, Decimal('45.50'), Decimal('45.50')),
                    ],
                },
                {
                    'vendor': vendor_objs[1],  # City Property
                    'invoice_number': 'CPM-2025-001',
                    'bill_date': date(2025, 1, 1),
                    'description': 'Office rent - January 2025',
                    'status': 'paid',
                    'lines': [
                        (rent_expense, 'Monthly office rent', 1, Decimal('2500.00'), Decimal('2500.00')),
                    ],
                },
                {
                    'vendor': vendor_objs[2],  # PG&E
                    'invoice_number': 'PGE-JAN2025',
                    'bill_date': date(2025, 1, 15),
                    'description': 'Electricity - January 2025',
                    'status': 'approved',
                    'lines': [
                        (utilities_expense, 'Electricity service', 1, Decimal('385.00'), Decimal('385.00')),
                    ],
                },
                {
                    'vendor': vendor_objs[3],  # Anderson CPA
                    'invoice_number': 'AC-2025-0042',
                    'bill_date': date(2025, 1, 10),
                    'description': 'Monthly bookkeeping services',
                    'status': 'approved',
                    'lines': [
                        (prof_services, 'Bookkeeping - January', 1, Decimal('1500.00'), Decimal('1500.00')),
                        (prof_services, 'Tax consultation', 2, Decimal('250.00'), Decimal('500.00')),
                    ],
                },
                {
                    'vendor': vendor_objs[4],  # CloudTech
                    'invoice_number': 'CT-2025-1001',
                    'bill_date': date(2025, 1, 20),
                    'description': 'Cloud hosting & SaaS licenses',
                    'status': 'pending_approval',
                    'lines': [
                        (tech_software, 'Cloud hosting (monthly)', 1, Decimal('299.00'), Decimal('299.00')),
                        (tech_software, 'SaaS license seats (10)', 10, Decimal('19.99'), Decimal('199.90')),
                    ],
                },
            ]

            bill_objs = []
            for i, bdata in enumerate(bills_data, start=1):
                bill_number = f"BILL-2025-{i:04d}"
                total = sum(line[4] for line in bdata['lines'])
                due_date = bdata['bill_date'] + timedelta(days=30)
                amount_paid = total if bdata['status'] == 'paid' else Decimal('0.00')

                bill, created = Bill.unscoped.get_or_create(
                    tenant=tenant,
                    bill_number=bill_number,
                    defaults={
                        'vendor': bdata['vendor'],
                        'vendor_invoice_number': bdata['invoice_number'],
                        'bill_date': bdata['bill_date'],
                        'due_date': due_date,
                        'subtotal': total,
                        'tax_amount': Decimal('0.00'),
                        'total_amount': total,
                        'amount_paid': amount_paid,
                        'ap_account': ap_account,
                        'fiscal_period': period,
                        'description': bdata['description'],
                        'status': bdata['status'],
                        'currency': usd,
                        'created_by': superuser,
                    }
                )
                bill_objs.append(bill)

                if created:
                    for account, desc, qty, unit_price, amount in bdata['lines']:
                        if account:
                            BillLine.objects.create(
                                bill=bill,
                                account=account,
                                description=desc,
                                quantity=qty,
                                unit_price=unit_price,
                                amount=amount,
                            )

            # --- Payments (for the paid bill) ---
            paid_bill = bill_objs[1]  # City Property rent
            pay_number = "PAY-2025-0001"
            payment, created = Payment.unscoped.get_or_create(
                tenant=tenant,
                payment_number=pay_number,
                defaults={
                    'vendor': paid_bill.vendor,
                    'payment_date': date(2025, 1, 12),
                    'amount': paid_bill.total_amount,
                    'payment_method': 'check',
                    'check_number': '10001',
                    'bank_account': checking,
                    'ap_account': ap_account,
                    'currency': usd,
                    'fiscal_period': period,
                    'status': 'completed',
                    'created_by': superuser,
                }
            )

            if created:
                PaymentAllocation.objects.create(
                    payment=payment,
                    bill=paid_bill,
                    amount=paid_bill.total_amount,
                )

            # --- Assign payment_term to bills for discount opportunities ---
            # Anderson CPA bill (index 3) uses 2/10 Net 30
            if bill_objs[3]:
                bill_objs[3].payment_term = term_map.get('2/10N30')
                bill_objs[3].bill_date = date.today() - timedelta(days=3)
                bill_objs[3].due_date = date.today() + timedelta(days=27)
                bill_objs[3].save()
            # PG&E bill (index 2) uses 1/10 Net 45
            if bill_objs[2]:
                bill_objs[2].payment_term = term_map.get('1/10N45')
                bill_objs[2].bill_date = date.today() - timedelta(days=2)
                bill_objs[2].due_date = date.today() + timedelta(days=43)
                bill_objs[2].save()
            # Staples bill (index 0) also gets 2/10 Net 30
            if bill_objs[0]:
                bill_objs[0].payment_term = term_map.get('2/10N30')
                bill_objs[0].bill_date = date.today() - timedelta(days=1)
                bill_objs[0].due_date = date.today() + timedelta(days=29)
                bill_objs[0].save()

            # --- Payment Batches ---
            batches_data = [
                {
                    'number': 'BATCH-2025-0001',
                    'description': 'January vendor payments - Checks',
                    'payment_date': date(2025, 1, 15),
                    'method': 'check',
                    'status': 'completed',
                    'total_amount': Decimal('2500.00'),
                    'payment_count': 1,
                },
                {
                    'number': 'BATCH-2025-0002',
                    'description': 'January ACH batch',
                    'payment_date': date(2025, 1, 25),
                    'method': 'ach',
                    'status': 'completed',
                    'total_amount': Decimal('684.90'),
                    'payment_count': 2,
                },
                {
                    'number': 'BATCH-2025-0003',
                    'description': 'February vendor payments - Checks',
                    'payment_date': date.today() + timedelta(days=5),
                    'method': 'check',
                    'status': 'ready',
                    'total_amount': Decimal('2000.00'),
                    'payment_count': 1,
                },
                {
                    'number': 'BATCH-2025-0004',
                    'description': 'February ACH batch',
                    'payment_date': date.today() + timedelta(days=7),
                    'method': 'ach',
                    'status': 'draft',
                    'total_amount': Decimal('498.90'),
                    'payment_count': 2,
                },
            ]

            for bdata in batches_data:
                PaymentBatch.unscoped.get_or_create(
                    tenant=tenant,
                    batch_number=bdata['number'],
                    defaults={
                        'description': bdata['description'],
                        'payment_date': bdata['payment_date'],
                        'payment_method': bdata['method'],
                        'bank_account': checking,
                        'status': bdata['status'],
                        'total_amount': bdata['total_amount'],
                        'payment_count': bdata['payment_count'],
                        'created_by': superuser,
                    }
                )

            # --- Bill Uploads ---
            uploads_data = [
                {
                    'number': 'UPL-2025-0001',
                    'filename': 'staples_invoice_jan2025.pdf',
                    'file_size': 245_760,
                    'mime_type': 'application/pdf',
                    'ocr_status': 'completed',
                    'extracted_data': {
                        'vendor_name': 'Staples Office Supply',
                        'invoice_number': 'INV-ST-20250105',
                        'invoice_date': '2025-01-05',
                        'total_amount': '$435.40',
                        'line_items': '3 items detected',
                    },
                    'bill': bill_objs[0],
                },
                {
                    'number': 'UPL-2025-0002',
                    'filename': 'city_property_rent_jan.pdf',
                    'file_size': 128_512,
                    'mime_type': 'application/pdf',
                    'ocr_status': 'completed',
                    'extracted_data': {
                        'vendor_name': 'City Property Management LLC',
                        'invoice_number': 'CPM-2025-001',
                        'invoice_date': '2025-01-01',
                        'total_amount': '$2,500.00',
                        'line_items': '1 item detected',
                    },
                    'bill': bill_objs[1],
                },
                {
                    'number': 'UPL-2025-0003',
                    'filename': 'pge_electric_jan2025.pdf',
                    'file_size': 98_304,
                    'mime_type': 'application/pdf',
                    'ocr_status': 'completed',
                    'extracted_data': {
                        'vendor_name': 'Pacific Gas & Electric',
                        'invoice_number': 'PGE-JAN2025',
                        'invoice_date': '2025-01-15',
                        'total_amount': '$385.00',
                    },
                    'bill': bill_objs[2],
                },
                {
                    'number': 'UPL-2025-0004',
                    'filename': 'anderson_cpa_feb_invoice.pdf',
                    'file_size': 312_000,
                    'mime_type': 'application/pdf',
                    'ocr_status': 'pending',
                    'extracted_data': {},
                    'bill': None,
                },
                {
                    'number': 'UPL-2025-0005',
                    'filename': 'cloudtech_hosting_receipt.png',
                    'file_size': 1_048_576,
                    'mime_type': 'image/png',
                    'ocr_status': 'processing',
                    'extracted_data': {},
                    'bill': None,
                },
                {
                    'number': 'UPL-2025-0006',
                    'filename': 'blurry_scan_receipt.jpg',
                    'file_size': 2_097_152,
                    'mime_type': 'image/jpeg',
                    'ocr_status': 'failed',
                    'extracted_data': {},
                    'bill': None,
                },
            ]

            for udata in uploads_data:
                BillUpload.unscoped.get_or_create(
                    tenant=tenant,
                    upload_number=udata['number'],
                    defaults={
                        'file': f"ap/bill_uploads/2025/01/{udata['filename']}",
                        'original_filename': udata['filename'],
                        'file_size': udata['file_size'],
                        'mime_type': udata['mime_type'],
                        'ocr_status': udata['ocr_status'],
                        'extracted_data': udata['extracted_data'],
                        'bill': udata['bill'],
                        'uploaded_by': superuser,
                    }
                )

            # --- Scheduled Payments ---
            approved_bills = [b for b in bill_objs if b.status == 'approved']
            schedules_data = [
                {
                    'bill': approved_bills[0] if len(approved_bills) > 0 else None,
                    'scheduled_date': date.today() + timedelta(days=3),
                    'priority': 'high',
                    'status': 'scheduled',
                    'notes': 'Early payment to capture 2% discount',
                },
                {
                    'bill': approved_bills[1] if len(approved_bills) > 1 else None,
                    'scheduled_date': date.today() + timedelta(days=7),
                    'priority': 'medium',
                    'status': 'scheduled',
                    'notes': 'Regular payment cycle',
                },
                {
                    'bill': approved_bills[2] if len(approved_bills) > 2 else None,
                    'scheduled_date': date.today() + timedelta(days=7),
                    'priority': 'medium',
                    'status': 'scheduled',
                    'notes': 'Grouped with other ACH payments',
                },
                {
                    'bill': bill_objs[1],  # paid bill - executed schedule
                    'scheduled_date': date(2025, 1, 12),
                    'priority': 'high',
                    'status': 'executed',
                    'notes': 'Rent payment - executed on time',
                },
            ]

            for sdata in schedules_data:
                if sdata['bill'] is None:
                    continue
                ScheduledPayment.unscoped.get_or_create(
                    tenant=tenant,
                    bill=sdata['bill'],
                    scheduled_date=sdata['scheduled_date'],
                    defaults={
                        'amount': sdata['bill'].total_amount - sdata['bill'].amount_paid,
                        'priority': sdata['priority'],
                        'status': sdata['status'],
                        'notes': sdata['notes'],
                        'payment': payment if sdata['status'] == 'executed' else None,
                        'created_by': superuser,
                    }
                )

        self.stdout.write(
            f'  Created AP data (terms, vendors, bills, payments, '
            f'batches, uploads, schedules)'
        )

    def _seed_ar_data(self):
        """Seed accounts receivable data: customers, invoices, receipts,
        recurring templates, collection activities."""
        from apps.accounts_receivable.models import (
            Customer, CustomerContact, Invoice, InvoiceLine, InvoiceApproval,
            Receipt, ReceiptAllocation,
            RecurringInvoiceTemplate, RecurringInvoiceTemplateLine,
            CreditMemo, CollectionActivity, CustomerPortalToken,
        )
        from apps.accounts_payable.models import PaymentTerm
        from apps.general_ledger.models import Account

        superuser = CustomUser.objects.filter(email='admin@navaccounting.com').first()
        if not superuser:
            self.stdout.write('  No superuser found, skipping AR seed.')
            return

        usd = Currency.objects.filter(code='USD').first()

        for tenant in Tenant.objects.all():
            # Lookup GL accounts
            ar_account = Account.unscoped.filter(
                tenant=tenant, account_number='1210'
            ).first()
            checking = Account.unscoped.filter(
                tenant=tenant, account_number='1110'
            ).first()
            revenue_sales = Account.unscoped.filter(
                tenant=tenant, account_number='4100'
            ).first()
            revenue_services = Account.unscoped.filter(
                tenant=tenant, account_number='4200'
            ).first()

            if not ar_account or not checking:
                self.stdout.write(f'  Skipping {tenant.name}: missing AR or checking account')
                continue

            # Lookup payment terms (reuse from AP)
            net30 = PaymentTerm.unscoped.filter(tenant=tenant, code='NET30').first()
            net15 = PaymentTerm.unscoped.filter(tenant=tenant, code='NET15').first()
            two_ten_net30 = PaymentTerm.unscoped.filter(tenant=tenant, code='2/10N30').first()

            fy = FiscalYear.unscoped.filter(tenant=tenant, is_current=True).first()
            period = FiscalPeriod.unscoped.filter(
                fiscal_year=fy, tenant=tenant, period_number=1
            ).first() if fy else None

            # --- Customers ---
            customers_data = [
                {
                    'company_name': 'Acme Corporation',
                    'display_name': 'Acme Corp',
                    'customer_type': 'business',
                    'tax_id': '11-1111111',
                    'payment_term': net30,
                    'credit_limit': Decimal('50000.00'),
                    'contacts': [
                        ('John', 'Smith', 'Procurement Manager', 'john@acme.example.com', '555-1001', True, True),
                    ],
                },
                {
                    'company_name': 'Global Enterprises Inc',
                    'display_name': 'Global Enterprises',
                    'customer_type': 'business',
                    'tax_id': '22-2222222',
                    'payment_term': two_ten_net30,
                    'credit_limit': Decimal('100000.00'),
                    'contacts': [
                        ('Maria', 'Garcia', 'CFO', 'maria@global.example.com', '555-2001', True, True),
                        ('Tom', 'Wilson', 'AP Clerk', 'tom@global.example.com', '555-2002', False, False),
                    ],
                },
                {
                    'company_name': 'Smith & Associates LLC',
                    'display_name': 'Smith & Associates',
                    'customer_type': 'business',
                    'tax_id': '33-3333333',
                    'payment_term': net15,
                    'credit_limit': Decimal('25000.00'),
                    'contacts': [
                        ('Robert', 'Smith', 'Owner', 'robert@smithllc.example.com', '555-3001', True, True),
                    ],
                },
                {
                    'company_name': 'Pacific Coast Trading Co',
                    'display_name': 'Pacific Coast Trading',
                    'customer_type': 'business',
                    'tax_id': '44-4444444',
                    'payment_term': net30,
                    'credit_limit': Decimal('75000.00'),
                    'contacts': [
                        ('Jennifer', 'Lee', 'Purchasing Director', 'jennifer@pacificcoast.example.com', '555-4001', True, True),
                    ],
                },
                {
                    'company_name': 'City of Springfield',
                    'display_name': 'City of Springfield',
                    'customer_type': 'government',
                    'tax_id': '55-5555555',
                    'payment_term': net30,
                    'credit_limit': Decimal('200000.00'),
                    'contacts': [
                        ('Linda', 'Brown', 'Finance Director', 'linda@springfield.gov.example.com', '555-5001', True, True),
                    ],
                },
            ]

            customer_objs = []
            for i, cdata in enumerate(customers_data, start=1):
                customer_number = f"CUST-{i:04d}"
                customer, created = Customer.unscoped.get_or_create(
                    tenant=tenant,
                    customer_number=customer_number,
                    defaults={
                        'company_name': cdata['company_name'],
                        'display_name': cdata['display_name'],
                        'customer_type': cdata['customer_type'],
                        'tax_id': cdata['tax_id'],
                        'billing_address_line_1': fake.street_address(),
                        'billing_city': fake.city(),
                        'billing_state': fake.state_abbr(),
                        'billing_postal_code': fake.zipcode(),
                        'billing_country': 'US',
                        'phone': fake.phone_number()[:20],
                        'email': f"billing@{cdata['display_name'].lower().replace(' ', '').replace('&', '')}.example.com",
                        'default_payment_term': cdata['payment_term'],
                        'default_revenue_account': revenue_sales or revenue_services,
                        'currency': usd,
                        'credit_limit': cdata['credit_limit'],
                        'preferred_payment_method': 'ach',
                    }
                )
                customer_objs.append(customer)

                if created:
                    for first, last, title, email, phone, is_primary, is_billing in cdata['contacts']:
                        CustomerContact.objects.get_or_create(
                            customer=customer,
                            email=email,
                            defaults={
                                'first_name': first,
                                'last_name': last,
                                'title': title,
                                'phone': phone,
                                'is_primary': is_primary,
                                'is_billing_contact': is_billing,
                            }
                        )

                    # Create portal token for first customer
                    if i == 1:
                        CustomerPortalToken.unscoped.get_or_create(
                            tenant=tenant,
                            customer=customer,
                            defaults={
                                'is_active': True,
                                'expires_at': timezone.now() + timedelta(days=365),
                            }
                        )

            # --- Invoices ---
            if not period:
                continue

            invoices_data = [
                {
                    'customer': customer_objs[0],  # Acme Corp
                    'invoice_date': date(2026, 1, 5),
                    'description': 'Consulting services - January',
                    'status': 'sent',
                    'lines': [
                        (revenue_services, 'Strategy consulting (40 hrs)', 40, Decimal('150.00'), Decimal('6000.00')),
                        (revenue_services, 'Research & analysis', 1, Decimal('2500.00'), Decimal('2500.00')),
                    ],
                },
                {
                    'customer': customer_objs[1],  # Global Enterprises
                    'invoice_date': date(2026, 1, 10),
                    'description': 'Software licenses - Q1',
                    'status': 'paid',
                    'lines': [
                        (revenue_sales, 'Enterprise license (annual)', 1, Decimal('12000.00'), Decimal('12000.00')),
                        (revenue_sales, 'Support package', 1, Decimal('3000.00'), Decimal('3000.00')),
                    ],
                },
                {
                    'customer': customer_objs[2],  # Smith & Associates
                    'invoice_date': date(2026, 1, 15),
                    'description': 'Legal research services',
                    'status': 'sent',
                    'lines': [
                        (revenue_services, 'Legal research (20 hrs)', 20, Decimal('200.00'), Decimal('4000.00')),
                    ],
                },
                {
                    'customer': customer_objs[3],  # Pacific Coast Trading
                    'invoice_date': date(2026, 2, 1),
                    'description': 'Product shipment - February',
                    'status': 'approved',
                    'lines': [
                        (revenue_sales, 'Widget A (100 units)', 100, Decimal('45.00'), Decimal('4500.00')),
                        (revenue_sales, 'Widget B (50 units)', 50, Decimal('85.00'), Decimal('4250.00')),
                        (revenue_sales, 'Shipping & handling', 1, Decimal('250.00'), Decimal('250.00')),
                    ],
                },
                {
                    'customer': customer_objs[0],  # Acme Corp (second invoice)
                    'invoice_date': date(2026, 2, 15),
                    'description': 'Consulting services - February',
                    'status': 'draft',
                    'lines': [
                        (revenue_services, 'Implementation consulting (60 hrs)', 60, Decimal('150.00'), Decimal('9000.00')),
                    ],
                },
                {
                    'customer': customer_objs[4],  # City of Springfield
                    'invoice_date': date(2025, 11, 1),
                    'description': 'Government contract services - Nov',
                    'status': 'partially_paid',
                    'lines': [
                        (revenue_services, 'Infrastructure audit', 1, Decimal('15000.00'), Decimal('15000.00')),
                        (revenue_services, 'Compliance review', 1, Decimal('5000.00'), Decimal('5000.00')),
                    ],
                },
            ]

            invoice_objs = []
            for i, idata in enumerate(invoices_data, start=1):
                invoice_number = f"INV-2026-{i:04d}"
                total = sum(line[4] for line in idata['lines'])
                due_days = 30
                if idata['customer'].default_payment_term:
                    due_days = idata['customer'].default_payment_term.due_days
                due_date = idata['invoice_date'] + timedelta(days=due_days)

                if idata['status'] == 'paid':
                    amount_paid = total
                elif idata['status'] == 'partially_paid':
                    amount_paid = Decimal('10000.00')
                else:
                    amount_paid = Decimal('0.00')

                invoice, created = Invoice.unscoped.get_or_create(
                    tenant=tenant,
                    invoice_number=invoice_number,
                    defaults={
                        'customer': idata['customer'],
                        'invoice_date': idata['invoice_date'],
                        'due_date': due_date,
                        'payment_term': idata['customer'].default_payment_term,
                        'subtotal': total,
                        'tax_amount': Decimal('0.00'),
                        'total_amount': total,
                        'amount_paid': amount_paid,
                        'ar_account': ar_account,
                        'fiscal_period': period,
                        'description': idata['description'],
                        'status': idata['status'],
                        'currency': usd,
                        'created_by': superuser,
                        'sent_date': idata['invoice_date'] if idata['status'] in ['sent', 'paid', 'partially_paid'] else None,
                    }
                )
                invoice_objs.append(invoice)

                if created:
                    for account, desc, qty, unit_price, amount in idata['lines']:
                        if account:
                            InvoiceLine.objects.create(
                                invoice=invoice,
                                account=account,
                                description=desc,
                                quantity=qty,
                                unit_price=unit_price,
                                amount=amount,
                            )

            # --- Receipts (for the paid invoice) ---
            paid_invoice = invoice_objs[1]  # Global Enterprises
            rct_number = "RCT-2026-0001"
            receipt, created = Receipt.unscoped.get_or_create(
                tenant=tenant,
                receipt_number=rct_number,
                defaults={
                    'customer': paid_invoice.customer,
                    'receipt_date': date(2026, 1, 18),
                    'amount': paid_invoice.total_amount,
                    'payment_method': 'ach',
                    'reference': 'ACH-20260118-001',
                    'bank_account': checking,
                    'ar_account': ar_account,
                    'currency': usd,
                    'fiscal_period': period,
                    'status': 'completed',
                    'created_by': superuser,
                }
            )

            if created:
                ReceiptAllocation.objects.create(
                    receipt=receipt,
                    invoice=paid_invoice,
                    amount=paid_invoice.total_amount,
                )

            # Partial payment receipt for City of Springfield
            partial_invoice = invoice_objs[5]  # City of Springfield
            rct_number_2 = "RCT-2026-0002"
            Receipt.unscoped.get_or_create(
                tenant=tenant,
                receipt_number=rct_number_2,
                defaults={
                    'customer': partial_invoice.customer,
                    'receipt_date': date(2025, 12, 1),
                    'amount': Decimal('10000.00'),
                    'payment_method': 'check',
                    'check_number': '50001',
                    'bank_account': checking,
                    'ar_account': ar_account,
                    'currency': usd,
                    'fiscal_period': period,
                    'status': 'completed',
                    'created_by': superuser,
                }
            )

            # --- Recurring Invoice Template ---
            if revenue_services:
                RecurringInvoiceTemplate.unscoped.get_or_create(
                    tenant=tenant,
                    template_number='REC-2026-0001',
                    defaults={
                        'name': 'Monthly Retainer - Acme Corp',
                        'customer': customer_objs[0],
                        'frequency': 'monthly',
                        'start_date': date(2026, 1, 1),
                        'next_invoice_date': date(2026, 4, 1),
                        'occurrences_created': 3,
                        'payment_term': net30,
                        'ar_account': ar_account,
                        'currency': usd,
                        'description': 'Monthly consulting retainer',
                        'subtotal': Decimal('5000.00'),
                        'tax_amount': Decimal('0.00'),
                        'total_amount': Decimal('5000.00'),
                        'auto_send': True,
                        'status': 'active',
                        'created_by': superuser,
                    }
                )

            # --- Collection Activities ---
            # Smith & Associates - overdue invoice
            if len(invoice_objs) > 2:
                CollectionActivity.unscoped.get_or_create(
                    tenant=tenant,
                    customer=customer_objs[2],
                    invoice=invoice_objs[2],
                    activity_type='dunning_letter',
                    defaults={
                        'dunning_level': 1,
                        'subject': 'Payment Reminder - INV-2026-0003',
                        'description': 'Sent first payment reminder for overdue invoice.',
                        'is_resolved': False,
                        'created_by': superuser,
                    }
                )

            # City of Springfield - follow up on partial payment
            if len(invoice_objs) > 5:
                CollectionActivity.unscoped.get_or_create(
                    tenant=tenant,
                    customer=customer_objs[4],
                    invoice=invoice_objs[5],
                    activity_type='phone_call',
                    defaults={
                        'dunning_level': 2,
                        'subject': 'Follow up on remaining balance',
                        'description': 'Called finance director regarding remaining $10,000 balance. '
                                       'Promised payment by end of month.',
                        'contact_person': 'Linda Brown',
                        'promise_date': date.today() + timedelta(days=15),
                        'promise_amount': Decimal('10000.00'),
                        'is_resolved': False,
                        'created_by': superuser,
                    }
                )

            # --- Submitted Invoices (for Approval Queue) ---
            submitted_invoices_data = [
                {
                    'number': 'INV-2026-0007',
                    'customer': customer_objs[3],  # Pacific Coast Trading
                    'invoice_date': date(2026, 2, 20),
                    'description': 'Employee training services - Q1',
                    'lines': [
                        (revenue_services, 'On-site training (3 days)', 3, Decimal('1500.00'), Decimal('4500.00')),
                        (revenue_services, 'Training materials', 1, Decimal('2000.00'), Decimal('2000.00')),
                    ],
                },
                {
                    'number': 'INV-2026-0008',
                    'customer': customer_objs[1],  # Global Enterprises
                    'invoice_date': date(2026, 2, 25),
                    'description': 'Annual maintenance contract renewal',
                    'lines': [
                        (revenue_services, 'Platform maintenance (annual)', 1, Decimal('15000.00'), Decimal('15000.00')),
                        (revenue_services, 'Priority support add-on', 1, Decimal('3000.00'), Decimal('3000.00')),
                    ],
                },
                {
                    'number': 'INV-2026-0009',
                    'customer': customer_objs[4],  # City of Springfield
                    'invoice_date': date(2026, 3, 1),
                    'description': 'Q1 audit services - government',
                    'lines': [
                        (revenue_services, 'Financial audit (80 hrs)', 80, Decimal('125.00'), Decimal('10000.00')),
                        (revenue_services, 'Compliance report preparation', 1, Decimal('2000.00'), Decimal('2000.00')),
                    ],
                },
            ]

            submitted_invoice_objs = []
            for sdata in submitted_invoices_data:
                total = sum(line[4] for line in sdata['lines'])
                due_days = 30
                if sdata['customer'].default_payment_term:
                    due_days = sdata['customer'].default_payment_term.due_days
                due_date = sdata['invoice_date'] + timedelta(days=due_days)

                inv, created = Invoice.unscoped.get_or_create(
                    tenant=tenant,
                    invoice_number=sdata['number'],
                    defaults={
                        'customer': sdata['customer'],
                        'invoice_date': sdata['invoice_date'],
                        'due_date': due_date,
                        'payment_term': sdata['customer'].default_payment_term,
                        'subtotal': total,
                        'tax_amount': Decimal('0.00'),
                        'total_amount': total,
                        'amount_paid': Decimal('0.00'),
                        'ar_account': ar_account,
                        'fiscal_period': period,
                        'description': sdata['description'],
                        'status': 'submitted',
                        'currency': usd,
                        'created_by': superuser,
                    }
                )
                submitted_invoice_objs.append(inv)

                if created:
                    for account, desc, qty, unit_price, amount in sdata['lines']:
                        if account:
                            InvoiceLine.objects.create(
                                invoice=inv,
                                account=account,
                                description=desc,
                                quantity=qty,
                                unit_price=unit_price,
                                amount=amount,
                            )
                    # Create pending approval record
                    InvoiceApproval.unscoped.get_or_create(
                        tenant=tenant,
                        invoice=inv,
                        approver=superuser,
                        defaults={
                            'status': 'pending',
                            'comments': '',
                        }
                    )

            # --- Credit Memos ---
            credit_memos_data = [
                {
                    'number': 'CM-2026-0001',
                    'customer': customer_objs[0],  # Acme Corp
                    'invoice': None,
                    'memo_date': date(2026, 2, 10),
                    'amount': Decimal('500.00'),
                    'reason': 'Billing error on consulting hours — 2 hours overbilled in January invoice.',
                    'status': 'draft',
                },
                {
                    'number': 'CM-2026-0002',
                    'customer': customer_objs[1],  # Global Enterprises
                    'invoice': invoice_objs[1] if len(invoice_objs) > 1 else None,
                    'memo_date': date(2026, 2, 15),
                    'amount': Decimal('1200.00'),
                    'reason': 'Defective software license key — replacement issued, partial refund for downtime.',
                    'status': 'approved',
                },
                {
                    'number': 'CM-2026-0003',
                    'customer': customer_objs[2],  # Smith & Associates
                    'invoice': invoice_objs[2] if len(invoice_objs) > 2 else None,
                    'memo_date': date(2026, 1, 25),
                    'amount': Decimal('800.00'),
                    'reason': 'Duplicate billing adjustment — research hours billed on two invoices.',
                    'status': 'applied',
                },
                {
                    'number': 'CM-2026-0004',
                    'customer': customer_objs[3],  # Pacific Coast Trading
                    'invoice': None,
                    'memo_date': date(2026, 3, 1),
                    'amount': Decimal('350.00'),
                    'reason': 'Shipping damage credit — Widget B units arrived damaged in transit.',
                    'status': 'draft',
                },
            ]

            for cmdata in credit_memos_data:
                CreditMemo.unscoped.get_or_create(
                    tenant=tenant,
                    memo_number=cmdata['number'],
                    defaults={
                        'customer': cmdata['customer'],
                        'invoice': cmdata['invoice'],
                        'memo_date': cmdata['memo_date'],
                        'amount': cmdata['amount'],
                        'reason': cmdata['reason'],
                        'status': cmdata['status'],
                        'ar_account': ar_account,
                        'fiscal_period': period,
                        'created_by': superuser,
                    }
                )

            # --- Additional Recurring Invoice Templates ---
            if revenue_services:
                # Add template lines for existing REC-2026-0001
                existing_rec = RecurringInvoiceTemplate.unscoped.filter(
                    tenant=tenant, template_number='REC-2026-0001'
                ).first()
                if existing_rec and not existing_rec.lines.exists():
                    RecurringInvoiceTemplateLine.objects.create(
                        template=existing_rec,
                        account=revenue_services,
                        description='Monthly consulting retainer',
                        quantity=Decimal('1.0000'),
                        unit_price=Decimal('5000.00'),
                        amount=Decimal('5000.00'),
                    )

                additional_templates = [
                    {
                        'number': 'REC-2026-0002',
                        'name': 'Quarterly License Renewal - Global Enterprises',
                        'customer': customer_objs[1],
                        'frequency': 'quarterly',
                        'start_date': date(2026, 1, 1),
                        'next_invoice_date': date(2026, 4, 1),
                        'occurrences_created': 1,
                        'subtotal': Decimal('12000.00'),
                        'total_amount': Decimal('12000.00'),
                        'auto_send': False,
                        'status': 'active',
                        'lines': [
                            (revenue_sales, 'Enterprise license renewal (quarterly)', 1, Decimal('9000.00'), Decimal('9000.00')),
                            (revenue_services, 'Premium support (quarterly)', 1, Decimal('3000.00'), Decimal('3000.00')),
                        ],
                    },
                    {
                        'number': 'REC-2026-0003',
                        'name': 'Monthly Legal Retainer - Smith & Associates',
                        'customer': customer_objs[2],
                        'frequency': 'monthly',
                        'start_date': date(2026, 1, 1),
                        'next_invoice_date': date(2026, 3, 1),
                        'occurrences_created': 2,
                        'subtotal': Decimal('2500.00'),
                        'total_amount': Decimal('2500.00'),
                        'auto_send': True,
                        'status': 'paused',
                        'lines': [
                            (revenue_services, 'Legal research retainer (monthly)', 1, Decimal('2500.00'), Decimal('2500.00')),
                        ],
                    },
                    {
                        'number': 'REC-2026-0004',
                        'name': 'Annual Audit Contract - City of Springfield',
                        'customer': customer_objs[4],
                        'frequency': 'annual',
                        'start_date': date(2026, 1, 1),
                        'next_invoice_date': date(2027, 1, 1),
                        'occurrences_created': 1,
                        'subtotal': Decimal('50000.00'),
                        'total_amount': Decimal('50000.00'),
                        'auto_send': False,
                        'status': 'active',
                        'lines': [
                            (revenue_services, 'Annual financial audit', 1, Decimal('35000.00'), Decimal('35000.00')),
                            (revenue_services, 'Compliance review & report', 1, Decimal('15000.00'), Decimal('15000.00')),
                        ],
                    },
                ]

                for tdata in additional_templates:
                    rec_tmpl, created = RecurringInvoiceTemplate.unscoped.get_or_create(
                        tenant=tenant,
                        template_number=tdata['number'],
                        defaults={
                            'name': tdata['name'],
                            'customer': tdata['customer'],
                            'frequency': tdata['frequency'],
                            'start_date': tdata['start_date'],
                            'next_invoice_date': tdata['next_invoice_date'],
                            'occurrences_created': tdata['occurrences_created'],
                            'payment_term': tdata['customer'].default_payment_term,
                            'ar_account': ar_account,
                            'currency': usd,
                            'description': tdata['name'],
                            'subtotal': tdata['subtotal'],
                            'tax_amount': Decimal('0.00'),
                            'total_amount': tdata['total_amount'],
                            'auto_send': tdata['auto_send'],
                            'status': tdata['status'],
                            'created_by': superuser,
                        }
                    )
                    if created:
                        for account, desc, qty, unit_price, amount in tdata['lines']:
                            if account:
                                RecurringInvoiceTemplateLine.objects.create(
                                    template=rec_tmpl,
                                    account=account,
                                    description=desc,
                                    quantity=Decimal(str(qty)),
                                    unit_price=unit_price,
                                    amount=amount,
                                )

            # --- Overdue Invoices (for Collections Dashboard aging buckets) ---
            overdue_invoices_data = [
                {
                    'number': 'INV-2026-0010',
                    'customer': customer_objs[0],  # Acme Corp
                    'invoice_date': date(2026, 1, 15),
                    'due_date': date(2026, 2, 15),  # ~17 days overdue → 1-30 bucket
                    'description': 'Consulting services - special project',
                    'lines': [
                        (revenue_services, 'Project discovery & planning (24 hrs)', 24, Decimal('200.00'), Decimal('4800.00')),
                        (revenue_services, 'Technical documentation', 1, Decimal('2400.00'), Decimal('2400.00')),
                    ],
                },
                {
                    'number': 'INV-2026-0011',
                    'customer': customer_objs[3],  # Pacific Coast Trading
                    'invoice_date': date(2025, 12, 20),
                    'due_date': date(2026, 1, 20),  # ~43 days overdue → 31-60 bucket
                    'description': 'Product shipment - December order',
                    'lines': [
                        (revenue_sales, 'Widget C (75 units)', 75, Decimal('65.00'), Decimal('4875.00')),
                        (revenue_sales, 'Express shipping', 1, Decimal('925.00'), Decimal('925.00')),
                    ],
                },
                {
                    'number': 'INV-2026-0012',
                    'customer': customer_objs[1],  # Global Enterprises
                    'invoice_date': date(2025, 11, 10),
                    'due_date': date(2025, 12, 10),  # ~84 days overdue → 61-90 bucket
                    'description': 'Custom integration development',
                    'lines': [
                        (revenue_services, 'API integration (35 hrs)', 35, Decimal('100.00'), Decimal('3500.00')),
                    ],
                },
                {
                    'number': 'INV-2026-0013',
                    'customer': customer_objs[2],  # Smith & Associates
                    'invoice_date': date(2025, 10, 1),
                    'due_date': date(2025, 11, 1),  # ~123 days overdue → 90+ bucket
                    'description': 'Legal research - regulatory compliance',
                    'lines': [
                        (revenue_services, 'Regulatory compliance research (40 hrs)', 40, Decimal('200.00'), Decimal('8000.00')),
                        (revenue_services, 'Expert consultation', 1, Decimal('3000.00'), Decimal('3000.00')),
                    ],
                },
            ]

            for odata in overdue_invoices_data:
                total = sum(line[4] for line in odata['lines'])
                inv, created = Invoice.unscoped.get_or_create(
                    tenant=tenant,
                    invoice_number=odata['number'],
                    defaults={
                        'customer': odata['customer'],
                        'invoice_date': odata['invoice_date'],
                        'due_date': odata['due_date'],
                        'payment_term': odata['customer'].default_payment_term,
                        'subtotal': total,
                        'tax_amount': Decimal('0.00'),
                        'total_amount': total,
                        'amount_paid': Decimal('0.00'),
                        'ar_account': ar_account,
                        'fiscal_period': period,
                        'description': odata['description'],
                        'status': 'sent',
                        'currency': usd,
                        'created_by': superuser,
                        'sent_date': odata['invoice_date'],
                    }
                )
                if created:
                    for account, desc, qty, unit_price, amount in odata['lines']:
                        if account:
                            InvoiceLine.objects.create(
                                invoice=inv,
                                account=account,
                                description=desc,
                                quantity=qty,
                                unit_price=unit_price,
                                amount=amount,
                            )

            # --- Additional Collection Activities ---
            # Email reminder for Acme Corp (overdue invoice INV-2026-0010)
            overdue_inv_acme = Invoice.unscoped.filter(
                tenant=tenant, invoice_number='INV-2026-0010'
            ).first()
            if overdue_inv_acme:
                CollectionActivity.unscoped.get_or_create(
                    tenant=tenant,
                    customer=customer_objs[0],
                    invoice=overdue_inv_acme,
                    activity_type='email',
                    defaults={
                        'dunning_level': 1,
                        'subject': 'Friendly Reminder - INV-2026-0010 Past Due',
                        'description': 'Sent email reminder to John Smith regarding overdue balance of $7,200.',
                        'contact_person': 'John Smith',
                        'follow_up_date': date(2026, 3, 10),
                        'is_resolved': False,
                        'created_by': superuser,
                    }
                )

            # Dispute from Pacific Coast Trading (INV-2026-0011)
            overdue_inv_pacific = Invoice.unscoped.filter(
                tenant=tenant, invoice_number='INV-2026-0011'
            ).first()
            if overdue_inv_pacific:
                CollectionActivity.unscoped.get_or_create(
                    tenant=tenant,
                    customer=customer_objs[3],
                    invoice=overdue_inv_pacific,
                    activity_type='dispute',
                    defaults={
                        'dunning_level': 2,
                        'subject': 'Billing Dispute - INV-2026-0011',
                        'description': 'Customer disputes shipping charges of $925. '
                                       'Claims express shipping was not authorized. Investigating.',
                        'contact_person': 'Jennifer Lee',
                        'follow_up_date': date(2026, 3, 15),
                        'is_resolved': False,
                        'created_by': superuser,
                    }
                )

            # Promise to pay from Global Enterprises (INV-2026-0012)
            overdue_inv_global = Invoice.unscoped.filter(
                tenant=tenant, invoice_number='INV-2026-0012'
            ).first()
            if overdue_inv_global:
                CollectionActivity.unscoped.get_or_create(
                    tenant=tenant,
                    customer=customer_objs[1],
                    invoice=overdue_inv_global,
                    activity_type='promise_to_pay',
                    defaults={
                        'dunning_level': 3,
                        'subject': 'Urgent Collection - INV-2026-0012',
                        'description': 'Spoke with CFO Maria Garcia. Account is 84 days past due. '
                                       'Promised full payment of $3,500 by March 20th.',
                        'contact_person': 'Maria Garcia',
                        'promise_date': date(2026, 3, 20),
                        'promise_amount': Decimal('3500.00'),
                        'is_resolved': False,
                        'created_by': superuser,
                    }
                )

        self.stdout.write(
            f'  Created AR data (customers, invoices, receipts, '
            f'recurring templates, credit memos, collection activities)'
        )
