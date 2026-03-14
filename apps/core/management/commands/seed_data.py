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
    python manage.py seed_data --ic         # Seed inventory & cost management
    python manage.py seed_data --pr         # Seed payroll integration
    python manage.py seed_data --pj         # Seed project/job costing
    python manage.py seed_data --me         # Seed multi-entity & consolidation
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
        parser.add_argument('--cm', action='store_true', help='Seed cash management data only')
        parser.add_argument('--fa', action='store_true', help='Seed fixed assets data only')
        parser.add_argument('--ic', action='store_true', help='Seed inventory & cost management data only')
        parser.add_argument('--pr', action='store_true', help='Seed payroll integration data only')
        parser.add_argument('--pj', action='store_true', help='Seed project/job costing data only')
        parser.add_argument('--me', action='store_true', help='Seed multi-entity & consolidation data only')
        parser.add_argument('--tx', action='store_true', help='Seed tax management data only')

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Cleaning existing data...')
            self._clean()

        seed_all = not any([
            options['tenants'], options['users'], options['company'],
            options['coa'], options['dashboard'], options['gl'], options['ap'],
            options['ar'], options['cm'], options['fa'], options['ic'],
            options['pr'], options['pj'], options['me'], options['tx'],
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

        if seed_all or options['cm']:
            self.stdout.write('Seeding cash management data...')
            self._seed_cm_data()

        if seed_all or options['fa']:
            self.stdout.write('Seeding fixed assets data...')
            self._seed_fa_data()

        if seed_all or options['ic']:
            self.stdout.write('Seeding inventory & cost management data...')
            self._seed_ic_data()

        if seed_all or options['pr']:
            self.stdout.write('Seeding payroll integration data...')
            self._seed_pr_data()

        if seed_all or options['pj']:
            self.stdout.write('Seeding project/job costing data...')
            self._seed_pj_data()

        if seed_all or options['me']:
            self.stdout.write('Seeding multi-entity & consolidation data...')
            self._seed_me_data()

        if seed_all or options['tx']:
            self.stdout.write('Seeding tax management data...')
            self._seed_tx_data()

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

    def _clean(self):
        # Clean TX (Tax Management) data first
        try:
            from apps.tax.models import (
                NexusActivity, NexusJurisdiction,
                AuditDocument, AuditFinding, TaxAudit,
                TaxDeadlineReminder, TaxDeadline,
                ETRReconciliation, DeferredTaxItem, IncomeTaxProvision,
                UseTaxAccrual, UseTaxAssessment,
                TaxReturnPayment, TaxReturnLine, TaxReturn,
                TaxGroupMember, TaxGroup, TaxRule, TaxRate, TaxJurisdiction,
            )
            NexusActivity.unscoped.all().delete()
            NexusJurisdiction.unscoped.all().delete()
            AuditDocument.unscoped.all().delete()
            AuditFinding.unscoped.all().delete()
            TaxAudit.unscoped.all().delete()
            TaxDeadlineReminder.objects.all().delete()
            TaxDeadline.unscoped.all().delete()
            ETRReconciliation.objects.all().delete()
            DeferredTaxItem.objects.all().delete()
            IncomeTaxProvision.unscoped.all().delete()
            UseTaxAccrual.unscoped.all().delete()
            UseTaxAssessment.unscoped.all().delete()
            TaxReturnPayment.unscoped.all().delete()
            TaxReturnLine.objects.all().delete()
            TaxReturn.unscoped.all().delete()
            TaxGroupMember.objects.all().delete()
            TaxGroup.unscoped.all().delete()
            TaxRule.unscoped.all().delete()
            TaxRate.unscoped.all().delete()
            TaxJurisdiction.unscoped.all().delete()
        except Exception:
            pass

        # Clean ME (Multi-Entity & Consolidation) data first
        try:
            from apps.multi_entity.models import (
                RegulatoryReport, LocalGAAPAdjustment,
                TransferPricingTransaction, TransferPricingPolicy,
                MinorityInterest, EliminationEntry, EliminationRule,
                ConsolidationRun, ConsolidationGroup,
                TranslationAdjustment, CurrencyTranslationRule,
                IntercompanyBalance, IntercompanyTransaction, Entity,
            )
            RegulatoryReport.unscoped.all().delete()
            LocalGAAPAdjustment.unscoped.all().delete()
            TransferPricingTransaction.unscoped.all().delete()
            TransferPricingPolicy.unscoped.all().delete()
            MinorityInterest.unscoped.all().delete()
            EliminationEntry.unscoped.all().delete()
            ConsolidationRun.unscoped.all().delete()
            EliminationRule.unscoped.all().delete()
            ConsolidationGroup.unscoped.all().delete()
            TranslationAdjustment.unscoped.all().delete()
            CurrencyTranslationRule.unscoped.all().delete()
            IntercompanyBalance.unscoped.all().delete()
            IntercompanyTransaction.unscoped.all().delete()
            Entity.unscoped.all().delete()
        except Exception:
            pass

        # Clean PJ (Project/Job Costing) data first
        try:
            from apps.project_costing.models import (
                ProfitabilitySnapshot, ResourceAssignment,
                ProjectInvoiceLine, ProjectInvoice,
                RevenueRecognition, ProjectMilestone,
                ExpenseEntry, TimeEntry,
                BillingRule, ProjectBudget, WBSElement, Project,
            )
            ProfitabilitySnapshot.unscoped.all().delete()
            ResourceAssignment.unscoped.all().delete()
            ProjectInvoiceLine.objects.all().delete()
            ProjectInvoice.unscoped.all().delete()
            RevenueRecognition.unscoped.all().delete()
            ProjectMilestone.unscoped.all().delete()
            ExpenseEntry.unscoped.all().delete()
            TimeEntry.unscoped.all().delete()
            BillingRule.unscoped.all().delete()
            ProjectBudget.unscoped.all().delete()
            WBSElement.unscoped.all().delete()
            Project.unscoped.all().delete()
        except Exception:
            pass

        # Clean PR (Payroll) data first
        try:
            from apps.payroll.models import (
                PayrollReconciliation, WorkersCompAssignment, WorkersCompClass,
                Garnishment, EmployeeBenefit, BenefitPlan,
                TaxRemittance, TaxWithholding, PayrollJournalLine,
                PayrollJournal, Employee,
            )
            PayrollReconciliation.unscoped.all().delete()
            WorkersCompAssignment.objects.all().delete()
            WorkersCompClass.unscoped.all().delete()
            Garnishment.unscoped.all().delete()
            EmployeeBenefit.objects.all().delete()
            BenefitPlan.unscoped.all().delete()
            TaxRemittance.unscoped.all().delete()
            TaxWithholding.unscoped.all().delete()
            PayrollJournalLine.objects.all().delete()
            PayrollJournal.unscoped.all().delete()
            Employee.unscoped.all().delete()
        except Exception:
            pass

        # Clean IC data first (depends on AP vendors and GL accounts)
        try:
            from apps.inventory.models import (
                LandedCostAllocation, LandedCostLine, LandedCostVoucher,
                CycleCountItem, CycleCountSession, CycleCountPlan,
                ReorderSuggestion, COGSEntry, COGSCalculation,
                InventoryTransferLine, InventoryTransfer, InventoryTransaction,
                GoodsReceiptLine, GoodsReceipt, PurchaseOrderLine, PurchaseOrder,
                PurchaseRequisitionLine, PurchaseRequisition,
                CostLayer, Warehouse, Item, UnitOfMeasure, ItemCategory,
            )
            LandedCostAllocation.objects.all().delete()
            LandedCostLine.objects.all().delete()
            LandedCostVoucher.unscoped.all().delete()
            CycleCountItem.objects.all().delete()
            CycleCountSession.unscoped.all().delete()
            CycleCountPlan.unscoped.all().delete()
            ReorderSuggestion.unscoped.all().delete()
            COGSEntry.objects.all().delete()
            COGSCalculation.unscoped.all().delete()
            InventoryTransferLine.objects.all().delete()
            InventoryTransfer.unscoped.all().delete()
            InventoryTransaction.unscoped.all().delete()
            GoodsReceiptLine.objects.all().delete()
            GoodsReceipt.unscoped.all().delete()
            PurchaseOrderLine.objects.all().delete()
            PurchaseOrder.unscoped.all().delete()
            PurchaseRequisitionLine.objects.all().delete()
            PurchaseRequisition.unscoped.all().delete()
            CostLayer.unscoped.all().delete()
            Warehouse.unscoped.all().delete()
            Item.unscoped.all().delete()
            UnitOfMeasure.unscoped.all().delete()
            ItemCategory.unscoped.all().delete()
        except Exception:
            pass

        # Clean CM data first
        try:
            from apps.cash_management.models import (
                BankFee, IntercompanyTransfer, CashForecastLine, CashForecast,
                ReconciliationItem, AutoMatchRule, BankReconciliation,
                BankTransaction, BankFeed, BankAccountSignatory, BankAccount,
            )
            BankFee.unscoped.all().delete()
            IntercompanyTransfer.unscoped.all().delete()
            CashForecastLine.objects.all().delete()
            CashForecast.unscoped.all().delete()
            ReconciliationItem.objects.all().delete()
            AutoMatchRule.unscoped.all().delete()
            BankReconciliation.unscoped.all().delete()
            BankTransaction.unscoped.all().delete()
            BankFeed.unscoped.all().delete()
            BankAccountSignatory.objects.all().delete()
            BankAccount.unscoped.all().delete()
        except Exception:
            pass

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
            ('manage_bank_feeds', 'Manage Bank Feeds', 'cash_management'),
            ('view_cash_position', 'View Cash Position', 'cash_management'),
            ('manage_forecasts', 'Manage Cash Forecasts', 'cash_management'),
            ('manage_transfers', 'Manage Intercompany Transfers', 'cash_management'),
            ('approve_transfers', 'Approve Intercompany Transfers', 'cash_management'),
            ('view_bank_fees', 'View Bank Fees', 'cash_management'),
            ('view_assets', 'View Fixed Assets', 'fixed_assets'),
            ('manage_assets', 'Manage Fixed Assets', 'fixed_assets'),
            ('view_inventory', 'View Inventory & Cost Management', 'inventory'),
            ('manage_inventory', 'Manage Inventory & Cost Management', 'inventory'),
            ('view_tax', 'View Tax Management', 'tax'),
            ('manage_tax', 'Manage Tax Management', 'tax'),
            ('file_tax_returns', 'File Tax Returns', 'tax'),
            ('manage_tax_calendar', 'Manage Tax Calendar', 'tax'),
            ('manage_tax_audits', 'Manage Tax Audits', 'tax'),
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
        from apps.general_ledger.models import (
            Account, JournalEntry, JournalEntryLine, JournalApproval,
            ExchangeRate, AccountReconciliation, AllocationRule,
            AllocationRuleLine, AuditTrail,
        )

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

            # --- Journal Entries Pending Approval ---
            pending_entries_data = [
                {
                    'description': 'Marketing Campaign Expense - Q1',
                    'date': date(2026, 2, 20),
                    'reference': 'MKT-2026-Q1',
                    'lines': [
                        ('6400', Decimal('8500.00'), Decimal('0.00')),
                        ('1110', Decimal('0.00'), Decimal('8500.00')),
                    ],
                },
                {
                    'description': 'Equipment Purchase - Server Hardware',
                    'date': date(2026, 2, 25),
                    'reference': 'PO-2026-0042',
                    'lines': [
                        ('1500', Decimal('12000.00'), Decimal('0.00')),
                        ('1110', Decimal('0.00'), Decimal('12000.00')),
                    ],
                },
                {
                    'description': 'Quarterly Bonus Accrual',
                    'date': date(2026, 3, 1),
                    'reference': 'HR-BONUS-Q1',
                    'lines': [
                        ('6100', Decimal('15000.00'), Decimal('0.00')),
                        ('2100', Decimal('0.00'), Decimal('15000.00')),
                    ],
                },
                {
                    'description': 'Office Supplies Restock',
                    'date': date(2026, 3, 2),
                    'reference': 'SUP-2026-0018',
                    'lines': [
                        ('6300', Decimal('1750.00'), Decimal('0.00')),
                        ('1110', Decimal('0.00'), Decimal('1750.00')),
                    ],
                },
            ]

            for i, entry_data in enumerate(pending_entries_data, start=4):
                entry_number = f"JE-2025-{i:04d}"
                je, created = JournalEntry.unscoped.get_or_create(
                    tenant=tenant,
                    entry_number=entry_number,
                    defaults={
                        'date': entry_data['date'],
                        'description': entry_data['description'],
                        'reference': entry_data.get('reference', ''),
                        'fiscal_period': period,
                        'status': 'pending',
                        'source': 'manual',
                        'currency': usd,
                        'created_by': superuser,
                    }
                )
                if created:
                    for acc_code, debit, credit in entry_data['lines']:
                        account = Account.unscoped.filter(
                            tenant=tenant, account_number=acc_code
                        ).first()
                        if account:
                            JournalEntryLine.objects.create(
                                journal_entry=je,
                                account=account,
                                debit=debit,
                                credit=credit,
                            )
                    # Create pending approval record
                    JournalApproval.unscoped.get_or_create(
                        tenant=tenant,
                        journal_entry=je,
                        approver=superuser,
                        defaults={
                            'status': 'pending',
                            'comments': '',
                        }
                    )

            # --- Allocation Rules ---
            checking_acct = Account.unscoped.filter(
                tenant=tenant, account_number='1110'
            ).first()
            rent_acct = Account.unscoped.filter(
                tenant=tenant, account_number='6200'
            ).first()
            salary_acct = Account.unscoped.filter(
                tenant=tenant, account_number='6100'
            ).first()
            supplies_acct = Account.unscoped.filter(
                tenant=tenant, account_number='6300'
            ).first()
            marketing_acct = Account.unscoped.filter(
                tenant=tenant, account_number='6400'
            ).first()
            revenue_services_gl = Account.unscoped.filter(
                tenant=tenant, account_number='4200'
            ).first()
            revenue_sales_gl = Account.unscoped.filter(
                tenant=tenant, account_number='4100'
            ).first()

            allocation_rules_data = [
                {
                    'name': 'Overhead Cost Allocation',
                    'source_account': rent_acct,
                    'description': 'Allocate rent expense across departments based on headcount.',
                    'is_active': True,
                    'lines': [
                        (salary_acct, Decimal('40.0000'), Decimal('0.00')),
                        (marketing_acct, Decimal('25.0000'), Decimal('0.00')),
                        (supplies_acct, Decimal('35.0000'), Decimal('0.00')),
                    ],
                },
                {
                    'name': 'Revenue Split - Product vs Services',
                    'source_account': revenue_services_gl,
                    'description': 'Split blended revenue between product sales and service revenue.',
                    'is_active': True,
                    'lines': [
                        (revenue_sales_gl, Decimal('60.0000'), Decimal('0.00')),
                        (revenue_services_gl, Decimal('40.0000'), Decimal('0.00')),
                    ] if revenue_sales_gl and revenue_services_gl else [],
                },
                {
                    'name': 'Marketing Budget Allocation (Inactive)',
                    'source_account': marketing_acct,
                    'description': 'Distribute marketing budget to sub-categories. Currently paused.',
                    'is_active': False,
                    'lines': [
                        (supplies_acct, Decimal('50.0000'), Decimal('0.00')),
                        (rent_acct, Decimal('50.0000'), Decimal('0.00')),
                    ],
                },
            ]

            for rdata in allocation_rules_data:
                if not rdata['source_account']:
                    continue
                rule, created = AllocationRule.unscoped.get_or_create(
                    tenant=tenant,
                    name=rdata['name'],
                    defaults={
                        'source_account': rdata['source_account'],
                        'description': rdata['description'],
                        'is_active': rdata['is_active'],
                    }
                )
                if created:
                    for target_account, percentage, fixed_amount in rdata['lines']:
                        if target_account:
                            AllocationRuleLine.objects.create(
                                rule=rule,
                                target_account=target_account,
                                percentage=percentage,
                                fixed_amount=fixed_amount,
                            )

            # --- Account Reconciliation ---
            recon_accounts_data = [
                {
                    'account_number': '1110',
                    'expected_balance': Decimal('35000.00'),
                    'actual_balance': Decimal('35000.00'),
                    'notes': 'Bank statement matches GL. All transactions verified.',
                },
                {
                    'account_number': '1210',
                    'expected_balance': Decimal('15000.00'),
                    'actual_balance': Decimal('14750.00'),
                    'notes': 'Difference of $250 — pending receipt not yet posted.',
                },
                {
                    'account_number': '4200',
                    'expected_balance': Decimal('15000.00'),
                    'actual_balance': Decimal('15000.00'),
                    'notes': 'Service revenue reconciled with sales report.',
                },
                {
                    'account_number': '6200',
                    'expected_balance': Decimal('2500.00'),
                    'actual_balance': Decimal('2500.00'),
                    'notes': 'Rent expense confirmed with lease agreement.',
                },
                {
                    'account_number': '3300',
                    'expected_balance': Decimal('50000.00'),
                    'actual_balance': Decimal('50000.00'),
                    'notes': 'Equity account reconciled.',
                },
            ]

            for rdata in recon_accounts_data:
                account = Account.unscoped.filter(
                    tenant=tenant, account_number=rdata['account_number']
                ).first()
                if account:
                    recon, created = AccountReconciliation.unscoped.get_or_create(
                        tenant=tenant,
                        account=account,
                        fiscal_period=period,
                        defaults={
                            'expected_balance': rdata['expected_balance'],
                            'actual_balance': rdata['actual_balance'],
                            'notes': rdata['notes'],
                            'reconciled_by': superuser if rdata['expected_balance'] == rdata['actual_balance'] else None,
                            'reconciled_at': timezone.now() if rdata['expected_balance'] == rdata['actual_balance'] else None,
                        }
                    )

            # --- Audit Trail ---
            audit_entries_data = [
                {
                    'table_name': 'JournalEntry',
                    'record_id': 1,
                    'action': 'create',
                    'field_name': '',
                    'old_value': '',
                    'new_value': 'Created journal entry JE-2025-0001: Initial Capital Investment',
                },
                {
                    'table_name': 'JournalEntry',
                    'record_id': 1,
                    'action': 'update',
                    'field_name': 'status',
                    'old_value': 'draft',
                    'new_value': 'posted',
                },
                {
                    'table_name': 'Account',
                    'record_id': 1,
                    'action': 'update',
                    'field_name': 'description',
                    'old_value': '',
                    'new_value': 'Primary operating checking account',
                },
                {
                    'table_name': 'JournalEntry',
                    'record_id': 2,
                    'action': 'create',
                    'field_name': '',
                    'old_value': '',
                    'new_value': 'Created journal entry JE-2025-0002: Office Rent Payment',
                },
                {
                    'table_name': 'JournalEntry',
                    'record_id': 2,
                    'action': 'update',
                    'field_name': 'status',
                    'old_value': 'draft',
                    'new_value': 'posted',
                },
                {
                    'table_name': 'JournalEntry',
                    'record_id': 3,
                    'action': 'create',
                    'field_name': '',
                    'old_value': '',
                    'new_value': 'Created journal entry JE-2025-0003: Service Revenue from Client',
                },
                {
                    'table_name': 'JournalEntry',
                    'record_id': 3,
                    'action': 'update',
                    'field_name': 'status',
                    'old_value': 'draft',
                    'new_value': 'posted',
                },
                {
                    'table_name': 'Account',
                    'record_id': 2,
                    'action': 'update',
                    'field_name': 'is_active',
                    'old_value': 'True',
                    'new_value': 'False',
                },
                {
                    'table_name': 'Account',
                    'record_id': 2,
                    'action': 'update',
                    'field_name': 'is_active',
                    'old_value': 'False',
                    'new_value': 'True',
                },
                {
                    'table_name': 'JournalApproval',
                    'record_id': 1,
                    'action': 'create',
                    'field_name': '',
                    'old_value': '',
                    'new_value': 'Approval request created for JE-2025-0004',
                },
                {
                    'table_name': 'AccountReconciliation',
                    'record_id': 1,
                    'action': 'create',
                    'field_name': '',
                    'old_value': '',
                    'new_value': 'Reconciliation started for account 1110 - Checking',
                },
                {
                    'table_name': 'AccountReconciliation',
                    'record_id': 1,
                    'action': 'update',
                    'field_name': 'status',
                    'old_value': 'pending',
                    'new_value': 'reconciled',
                },
            ]

            for adata in audit_entries_data:
                AuditTrail.unscoped.create(
                    tenant=tenant,
                    table_name=adata['table_name'],
                    record_id=adata['record_id'],
                    action=adata['action'],
                    field_name=adata['field_name'],
                    old_value=adata['old_value'],
                    new_value=adata['new_value'],
                    user=superuser,
                    ip_address='127.0.0.1',
                )

        self.stdout.write(
            f'  Created GL data (accounts, exchange rates, journal entries, '
            f'approvals, allocations, reconciliations, audit trail)'
        )

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

    def _seed_cm_data(self):
        """Seed cash management data for each tenant."""
        from apps.cash_management.models import (
            BankAccount, BankAccountSignatory, BankFeed, BankTransaction,
            BankReconciliation, ReconciliationItem, AutoMatchRule,
            CashForecast, CashForecastLine, IntercompanyTransfer, BankFee,
        )
        from apps.general_ledger.models import Account

        superuser = CustomUser.objects.filter(is_superuser=True).first()
        if not superuser:
            return

        tenants = Tenant.objects.all()
        for tenant in tenants:
            usd = Currency.objects.filter(code='USD').first()
            if not usd:
                continue

            # Get GL bank/cash accounts
            checking_gl = Account.unscoped.filter(
                tenant=tenant, account_number='1110'
            ).first()
            savings_gl = Account.unscoped.filter(
                tenant=tenant, account_number='1120'
            ).first()
            petty_cash_gl = Account.unscoped.filter(
                tenant=tenant, account_number='1100'
            ).first()

            if not checking_gl:
                continue

            # --- Bank Accounts ---
            checking, _ = BankAccount.unscoped.get_or_create(
                tenant=tenant,
                account_number_display='BNK-0001',
                defaults={
                    'gl_account': checking_gl,
                    'bank_name': 'First National Bank',
                    'account_number': '4521893067',
                    'account_number_masked': '****3067',
                    'routing_number': '021000021',
                    'account_type': 'checking',
                    'currency': usd,
                    'opening_balance': Decimal('50000.00'),
                    'current_balance': Decimal('47250.00'),
                    'is_active': True,
                }
            )

            savings_acct = None
            if savings_gl:
                savings_acct, _ = BankAccount.unscoped.get_or_create(
                    tenant=tenant,
                    account_number_display='BNK-0002',
                    defaults={
                        'gl_account': savings_gl,
                        'bank_name': 'First National Bank',
                        'account_number': '4521893068',
                        'account_number_masked': '****3068',
                        'routing_number': '021000021',
                        'account_type': 'savings',
                        'currency': usd,
                        'opening_balance': Decimal('100000.00'),
                        'current_balance': Decimal('100000.00'),
                        'is_active': True,
                    }
                )

            credit_line = None
            if petty_cash_gl:
                credit_line, _ = BankAccount.unscoped.get_or_create(
                    tenant=tenant,
                    account_number_display='BNK-0003',
                    defaults={
                        'gl_account': petty_cash_gl,
                        'bank_name': 'Metro Business Bank',
                        'account_number': '7789012345',
                        'account_number_masked': '****2345',
                        'routing_number': '026009593',
                        'account_type': 'credit_line',
                        'currency': usd,
                        'opening_balance': Decimal('0.00'),
                        'current_balance': Decimal('-5000.00'),
                        'is_active': True,
                    }
                )

            # --- Signatories ---
            BankAccountSignatory.objects.get_or_create(
                bank_account=checking,
                name='John Smith',
                defaults={
                    'title': 'CEO',
                    'signature_level': 'primary',
                    'authorization_limit': Decimal('100000.00'),
                }
            )
            BankAccountSignatory.objects.get_or_create(
                bank_account=checking,
                name='Jane Doe',
                defaults={
                    'title': 'CFO',
                    'signature_level': 'primary',
                    'authorization_limit': Decimal('50000.00'),
                }
            )

            # --- Bank Feed ---
            BankFeed.unscoped.get_or_create(
                tenant=tenant,
                bank_account=checking,
                feed_source='manual_csv',
                defaults={
                    'status': 'active',
                    'notes': 'Manual CSV import for checking account',
                }
            )

            # --- Bank Transactions ---
            txn_data = [
                ('BTX-2026-0001', date(2026, 1, 5), Decimal('5000.00'), 'credit', 'Customer Payment - INV-2026-0001'),
                ('BTX-2026-0002', date(2026, 1, 8), Decimal('1250.00'), 'debit', 'Vendor Payment - Check #1042'),
                ('BTX-2026-0003', date(2026, 1, 12), Decimal('3500.00'), 'credit', 'Wire Transfer - Client ABC'),
                ('BTX-2026-0004', date(2026, 1, 15), Decimal('800.00'), 'debit', 'ACH - Utility Bill'),
                ('BTX-2026-0005', date(2026, 1, 20), Decimal('2200.00'), 'credit', 'Customer Payment - INV-2026-0003'),
                ('BTX-2026-0006', date(2026, 1, 22), Decimal('450.00'), 'debit', 'Office Supplies - Card'),
                ('BTX-2026-0007', date(2026, 1, 25), Decimal('6000.00'), 'credit', 'Transfer from Savings'),
                ('BTX-2026-0008', date(2026, 1, 28), Decimal('3200.00'), 'debit', 'Payroll - January'),
                ('BTX-2026-0009', date(2026, 2, 1), Decimal('1800.00'), 'credit', 'Customer Payment - INV-2026-0005'),
                ('BTX-2026-0010', date(2026, 2, 5), Decimal('950.00'), 'debit', 'Insurance Premium'),
                ('BTX-2026-0011', date(2026, 2, 10), Decimal('4200.00'), 'credit', 'Customer Payment - Wire'),
                ('BTX-2026-0012', date(2026, 2, 15), Decimal('1500.00'), 'debit', 'Rent Payment'),
                ('BTX-2026-0013', date(2026, 2, 18), Decimal('750.00'), 'debit', 'Software Subscription'),
                ('BTX-2026-0014', date(2026, 2, 22), Decimal('8500.00'), 'credit', 'Large Client Payment'),
                ('BTX-2026-0015', date(2026, 2, 28), Decimal('3200.00'), 'debit', 'Payroll - February'),
            ]
            for txn_num, txn_date, amount, txn_type, desc in txn_data:
                BankTransaction.unscoped.get_or_create(
                    tenant=tenant,
                    transaction_number=txn_num,
                    defaults={
                        'bank_account': checking,
                        'transaction_date': txn_date,
                        'amount': amount,
                        'transaction_type': txn_type,
                        'description': desc,
                        'is_matched': txn_num in ('BTX-2026-0001', 'BTX-2026-0002', 'BTX-2026-0003'),
                    }
                )

            # --- Auto Match Rules ---
            AutoMatchRule.unscoped.get_or_create(
                tenant=tenant,
                name='Exact Amount Match',
                defaults={
                    'rule_type': 'exact_amount',
                    'pattern': {'tolerance': 0},
                    'priority': 10,
                    'is_active': True,
                }
            )
            AutoMatchRule.unscoped.get_or_create(
                tenant=tenant,
                name='Reference Number Match',
                defaults={
                    'rule_type': 'reference_match',
                    'pattern': {'field': 'reference'},
                    'priority': 20,
                    'is_active': True,
                }
            )

            # --- Cash Forecast ---
            forecast, _ = CashForecast.unscoped.get_or_create(
                tenant=tenant,
                forecast_number='FCT-2026-0001',
                defaults={
                    'name': 'Q1 2026 Cash Forecast',
                    'forecast_type': 'short_term',
                    'start_date': date(2026, 1, 1),
                    'end_date': date(2026, 3, 31),
                    'created_by': superuser,
                    'status': 'active',
                }
            )
            forecast_lines = [
                (date(2026, 1, 15), 'ar_collections', 'January AR Collections', Decimal('25000.00'), Decimal('23500.00')),
                (date(2026, 1, 30), 'ap_payments', 'January AP Payments', Decimal('-18000.00'), Decimal('-17200.00')),
                (date(2026, 1, 31), 'payroll', 'January Payroll', Decimal('-12000.00'), Decimal('-12000.00')),
                (date(2026, 2, 15), 'ar_collections', 'February AR Collections', Decimal('28000.00'), Decimal('30100.00')),
                (date(2026, 2, 28), 'ap_payments', 'February AP Payments', Decimal('-20000.00'), Decimal('-19500.00')),
                (date(2026, 2, 28), 'payroll', 'February Payroll', Decimal('-12000.00'), Decimal('-12000.00')),
                (date(2026, 3, 1), 'tax', 'Q1 Estimated Tax', Decimal('-5000.00'), None),
                (date(2026, 3, 15), 'ar_collections', 'March AR Collections', Decimal('30000.00'), None),
                (date(2026, 3, 30), 'ap_payments', 'March AP Payments', Decimal('-22000.00'), None),
                (date(2026, 3, 31), 'payroll', 'March Payroll', Decimal('-12000.00'), None),
            ]
            for line_date, category, desc, expected, actual in forecast_lines:
                variance = Decimal('0.00')
                if actual is not None:
                    variance = actual - expected
                CashForecastLine.objects.get_or_create(
                    forecast=forecast,
                    line_date=line_date,
                    category=category,
                    defaults={
                        'description': desc,
                        'expected_amount': expected,
                        'actual_amount': actual,
                        'variance': variance,
                    }
                )

            # --- Intercompany Transfers ---
            if savings_acct:
                IntercompanyTransfer.unscoped.get_or_create(
                    tenant=tenant,
                    transfer_number='ICT-2026-0001',
                    defaults={
                        'from_bank_account': savings_acct,
                        'to_bank_account': checking,
                        'amount': Decimal('6000.00'),
                        'currency': usd,
                        'transfer_date': date(2026, 1, 25),
                        'reference': 'Cash sweep',
                        'status': 'completed',
                        'created_by': superuser,
                        'approved_by': superuser,
                    }
                )
                IntercompanyTransfer.unscoped.get_or_create(
                    tenant=tenant,
                    transfer_number='ICT-2026-0002',
                    defaults={
                        'from_bank_account': checking,
                        'to_bank_account': savings_acct,
                        'amount': Decimal('10000.00'),
                        'currency': usd,
                        'transfer_date': date(2026, 3, 1),
                        'reference': 'Excess cash to savings',
                        'status': 'draft',
                        'created_by': superuser,
                    }
                )

            # --- Bank Fees ---
            fee_data = [
                (date(2026, 1, 31), 'monthly_maintenance', 'Monthly Service Charge', Decimal('25.00'), True),
                (date(2026, 1, 15), 'wire', 'Incoming Wire Fee', Decimal('15.00'), False),
                (date(2026, 1, 22), 'transaction', 'ACH Processing Fee', Decimal('0.50'), False),
                (date(2026, 2, 5), 'foreign_exchange', 'FX Conversion Fee', Decimal('35.00'), False),
                (date(2026, 2, 28), 'monthly_maintenance', 'Monthly Service Charge', Decimal('25.00'), True),
                (date(2026, 2, 10), 'wire', 'Outgoing Wire Fee', Decimal('25.00'), False),
                (date(2026, 1, 20), 'overdraft', 'Overdraft Protection Fee', Decimal('35.00'), False),
                (date(2026, 2, 15), 'atm', 'Out-of-Network ATM', Decimal('3.00'), False),
            ]
            for fee_date, fee_type, desc, amount, recurring in fee_data:
                BankFee.unscoped.get_or_create(
                    tenant=tenant,
                    bank_account=checking,
                    fee_date=fee_date,
                    fee_type=fee_type,
                    defaults={
                        'description': desc,
                        'amount': amount,
                        'is_recurring': recurring,
                    }
                )

        self.stdout.write(
            f'  Created CM data (bank accounts, signatories, feeds, '
            f'transactions, match rules, forecasts, transfers, fees)'
        )

    def _seed_fa_data(self):
        """Seed fixed assets sample data."""
        from apps.fixed_assets.models import (
            AssetCategory, AssetLocation, Asset, AssetAcquisition,
            DepreciationProfile, AssetTransfer, AssetDisposal,
            ImpairmentTest, PhysicalInventory, PhysicalInventoryItem,
            TaxDepreciationBook, TaxDepreciationEntry,
        )
        from apps.fixed_assets.services import generate_depreciation_schedule

        tenants = Tenant.objects.all()
        if not tenants.exists():
            self.stdout.write('  No tenants found. Skipping FA seeding.')
            return

        for tenant in tenants:
            from apps.tenants.managers import set_current_tenant
            set_current_tenant(tenant)

            # Get GL accounts for category mapping
            from apps.general_ledger.models import Account
            gl_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )[:10])
            if len(gl_accounts) < 3:
                self.stdout.write(f'  Skipping FA for {tenant.name}: not enough GL accounts.')
                continue

            # Get currency
            default_currency = Currency.objects.first()
            if not default_currency:
                continue

            # Get a user
            users = list(CustomUser.objects.all()[:3])
            if not users:
                continue

            # --- Asset Categories ---
            categories_data = [
                {'code': 'BLDG', 'name': 'Buildings', 'method': 'straight_line', 'life': 360, 'salvage': Decimal('10.00')},
                {'code': 'VEHI', 'name': 'Vehicles', 'method': 'declining_balance', 'life': 60, 'salvage': Decimal('15.00')},
                {'code': 'FURN', 'name': 'Furniture & Fixtures', 'method': 'straight_line', 'life': 84, 'salvage': Decimal('5.00')},
                {'code': 'COMP', 'name': 'Computer Equipment', 'method': 'straight_line', 'life': 36, 'salvage': Decimal('0.00')},
                {'code': 'MACH', 'name': 'Machinery', 'method': 'units_of_production', 'life': 120, 'salvage': Decimal('5.00')},
            ]
            categories = []
            for i, cd in enumerate(categories_data):
                cat, _ = AssetCategory.unscoped.get_or_create(
                    tenant=tenant, code=cd['code'],
                    defaults={
                        'name': cd['name'],
                        'depreciation_method': cd['method'],
                        'default_useful_life_months': cd['life'],
                        'default_salvage_percentage': cd['salvage'],
                        'asset_gl_account': gl_accounts[min(i, len(gl_accounts) - 1)],
                        'depreciation_gl_account': gl_accounts[min(i + 1, len(gl_accounts) - 1)],
                        'accumulated_depreciation_gl_account': gl_accounts[min(i + 2, len(gl_accounts) - 1)],
                    }
                )
                categories.append(cat)

            # --- Asset Locations ---
            locations_data = [
                {'code': 'HQ', 'name': 'Head Office', 'address': '123 Main Street'},
                {'code': 'WH1', 'name': 'Warehouse 1', 'address': '456 Industrial Blvd'},
                {'code': 'BR1', 'name': 'Branch Office 1', 'address': '789 Commerce Ave'},
            ]
            locations = []
            for ld in locations_data:
                loc, _ = AssetLocation.unscoped.get_or_create(
                    tenant=tenant, code=ld['code'],
                    defaults={'name': ld['name'], 'address': ld['address']}
                )
                locations.append(loc)

            # --- Assets ---
            assets_data = [
                {'name': 'Office Building - Main', 'cat': 0, 'loc': 0, 'cost': Decimal('500000.00'), 'life': 360, 'salvage': Decimal('50000.00'), 'method': 'straight_line'},
                {'name': 'Delivery Van #1', 'cat': 1, 'loc': 1, 'cost': Decimal('35000.00'), 'life': 60, 'salvage': Decimal('5250.00'), 'method': 'declining_balance'},
                {'name': 'Executive Desk Set', 'cat': 2, 'loc': 0, 'cost': Decimal('2500.00'), 'life': 84, 'salvage': Decimal('125.00'), 'method': 'straight_line'},
                {'name': 'Dell Server Rack', 'cat': 3, 'loc': 0, 'cost': Decimal('15000.00'), 'life': 36, 'salvage': Decimal('0.00'), 'method': 'straight_line'},
                {'name': 'MacBook Pro Fleet (10 units)', 'cat': 3, 'loc': 0, 'cost': Decimal('25000.00'), 'life': 36, 'salvage': Decimal('2500.00'), 'method': 'straight_line'},
                {'name': 'CNC Milling Machine', 'cat': 4, 'loc': 1, 'cost': Decimal('85000.00'), 'life': 120, 'salvage': Decimal('4250.00'), 'method': 'units_of_production'},
                {'name': 'Conference Room Furniture', 'cat': 2, 'loc': 2, 'cost': Decimal('8000.00'), 'life': 84, 'salvage': Decimal('400.00'), 'method': 'straight_line'},
                {'name': 'Forklift', 'cat': 4, 'loc': 1, 'cost': Decimal('28000.00'), 'life': 96, 'salvage': Decimal('3000.00'), 'method': 'declining_balance'},
            ]
            assets = []
            for ad in assets_data:
                asset_number = Asset.generate_asset_number(tenant)
                acq_date = date.today() - timedelta(days=random.randint(90, 730))
                asset, created = Asset.unscoped.get_or_create(
                    tenant=tenant, name=ad['name'],
                    defaults={
                        'asset_number': asset_number,
                        'category': categories[ad['cat']],
                        'location': locations[ad['loc']],
                        'custodian': random.choice(users),
                        'serial_number': f'SN-{fake.bothify(text="####-????-####")}',
                        'barcode': f'BC{fake.numerify(text="##########")}',
                        'acquisition_date': acq_date,
                        'acquisition_cost': ad['cost'],
                        'salvage_value': ad['salvage'],
                        'useful_life_months': ad['life'],
                        'depreciation_method': ad['method'],
                        'status': 'in_service',
                        'manufacturer': fake.company(),
                        'model_number': fake.bothify(text='MOD-####'),
                    }
                )
                if created:
                    # Create depreciation profile
                    end_date = acq_date + timedelta(days=ad['life'] * 30)
                    DepreciationProfile.unscoped.get_or_create(
                        tenant=tenant, asset=asset,
                        defaults={
                            'method': ad['method'],
                            'useful_life_months': ad['life'],
                            'start_date': acq_date,
                            'end_date': end_date,
                            'salvage_value': ad['salvage'],
                            'total_units': 100000 if ad['method'] == 'units_of_production' else None,
                            'declining_balance_rate': Decimal('200.00') if ad['method'] == 'declining_balance' else Decimal('0.00'),
                        }
                    )
                    # Generate depreciation schedule
                    generate_depreciation_schedule(asset)

                assets.append(asset)

            # --- Acquisitions ---
            for asset in assets[:4]:
                AssetAcquisition.unscoped.get_or_create(
                    tenant=tenant, asset=asset,
                    defaults={
                        'acquisition_number': AssetAcquisition.generate_acquisition_number(tenant),
                        'acquisition_type': 'purchase',
                        'vendor_name': fake.company(),
                        'invoice_reference': f'INV-{fake.numerify(text="######")}',
                        'acquisition_date': asset.acquisition_date,
                        'amount': asset.acquisition_cost,
                        'currency': default_currency,
                        'is_capitalized': True,
                        'capitalization_date': asset.acquisition_date,
                    }
                )

            # --- Transfers ---
            if len(assets) >= 3:
                AssetTransfer.unscoped.get_or_create(
                    tenant=tenant, asset=assets[2],
                    transfer_number=AssetTransfer.generate_transfer_number(tenant),
                    defaults={
                        'from_location': locations[0],
                        'to_location': locations[2],
                        'transfer_date': date.today() - timedelta(days=30),
                        'reason': 'Relocated to branch office',
                        'status': 'completed',
                        'created_by': users[0],
                        'approved_by': users[0],
                    }
                )

            # --- Asset Disposals ---
            if len(assets) >= 7:
                disposals_data = [
                    {
                        'asset': assets[6],  # Conference Room Furniture
                        'disposal_type': 'sale',
                        'days_ago': 20,
                        'proceeds': Decimal('3500.00'),
                        'nbv': Decimal('5200.00'),
                        'buyer_name': fake.company(),
                        'invoice_ref': f'SALE-{fake.numerify(text="######")}',
                        'status': 'completed',
                        'notes': 'Sold old conference furniture to make room for renovation.',
                    },
                    {
                        'asset': assets[3],  # Dell Server Rack
                        'disposal_type': 'write_off',
                        'days_ago': 10,
                        'proceeds': Decimal('0.00'),
                        'nbv': Decimal('2500.00'),
                        'buyer_name': '',
                        'invoice_ref': '',
                        'status': 'completed',
                        'notes': 'Server hardware failure — beyond economical repair.',
                    },
                    {
                        'asset': assets[4],  # MacBook Pro Fleet
                        'disposal_type': 'donation',
                        'days_ago': 5,
                        'proceeds': Decimal('0.00'),
                        'nbv': Decimal('8000.00'),
                        'buyer_name': 'Local Community College',
                        'invoice_ref': '',
                        'status': 'pending',
                        'notes': 'Donating retired laptops to local school programme.',
                    },
                    {
                        'asset': assets[2],  # Executive Desk Set
                        'disposal_type': 'scrap',
                        'days_ago': 45,
                        'proceeds': Decimal('50.00'),
                        'nbv': Decimal('800.00'),
                        'buyer_name': '',
                        'invoice_ref': '',
                        'status': 'completed',
                        'notes': 'Desk damaged during office move; scrapped for parts.',
                    },
                ]
                for dd in disposals_data:
                    AssetDisposal.unscoped.get_or_create(
                        tenant=tenant, asset=dd['asset'],
                        disposal_number=AssetDisposal.generate_disposal_number(tenant),
                        defaults={
                            'disposal_type': dd['disposal_type'],
                            'disposal_date': date.today() - timedelta(days=dd['days_ago']),
                            'proceeds': dd['proceeds'],
                            'net_book_value_at_disposal': dd['nbv'],
                            'buyer_name': dd['buyer_name'],
                            'invoice_reference': dd['invoice_ref'],
                            'status': dd['status'],
                            'created_by': users[0],
                            'approved_by': users[0] if dd['status'] == 'completed' else None,
                            'notes': dd['notes'],
                        }
                    )

            # --- Impairment Tests ---
            if len(assets) >= 8:
                impairment_data = [
                    {
                        'asset': assets[0],  # Office Building - Main
                        'days_ago': 60,
                        'carrying_amount': Decimal('450000.00'),
                        'value_in_use': Decimal('420000.00'),
                        'fair_value_less_costs': Decimal('380000.00'),
                        'is_impaired': True,
                        'notes': 'Annual impairment review — local property values declined due to market downturn.',
                    },
                    {
                        'asset': assets[5],  # CNC Milling Machine
                        'days_ago': 30,
                        'carrying_amount': Decimal('70000.00'),
                        'value_in_use': Decimal('55000.00'),
                        'fair_value_less_costs': Decimal('48000.00'),
                        'is_impaired': True,
                        'notes': 'Technology obsolescence — newer CNC models significantly more efficient.',
                    },
                    {
                        'asset': assets[7],  # Forklift
                        'days_ago': 15,
                        'carrying_amount': Decimal('22000.00'),
                        'value_in_use': Decimal('25000.00'),
                        'fair_value_less_costs': Decimal('23000.00'),
                        'is_impaired': False,
                        'notes': 'Annual impairment review — recoverable amount exceeds carrying amount. No impairment.',
                    },
                    {
                        'asset': assets[1],  # Delivery Van #1
                        'days_ago': 7,
                        'carrying_amount': Decimal('28000.00'),
                        'value_in_use': Decimal('18000.00'),
                        'fair_value_less_costs': Decimal('20000.00'),
                        'is_impaired': True,
                        'notes': 'Vehicle involved in minor accident; estimated resale value reduced.',
                    },
                ]
                for imp in impairment_data:
                    recoverable = max(imp['value_in_use'], imp['fair_value_less_costs'])
                    loss = max(imp['carrying_amount'] - recoverable, Decimal('0.00'))
                    ImpairmentTest.unscoped.get_or_create(
                        tenant=tenant, asset=imp['asset'],
                        test_date=date.today() - timedelta(days=imp['days_ago']),
                        defaults={
                            'carrying_amount': imp['carrying_amount'],
                            'recoverable_amount': recoverable,
                            'value_in_use': imp['value_in_use'],
                            'fair_value_less_costs': imp['fair_value_less_costs'],
                            'impairment_loss': loss,
                            'is_impaired': imp['is_impaired'],
                            'created_by': users[0],
                            'notes': imp['notes'],
                        }
                    )

            # --- Tax Depreciation Book ---
            macrs_book, _ = TaxDepreciationBook.unscoped.get_or_create(
                tenant=tenant, code='MACRS',
                defaults={
                    'name': 'MACRS Tax Book',
                    'tax_method': 'macrs',
                    'description': 'Modified Accelerated Cost Recovery System',
                }
            )

            for asset in assets[:3]:
                TaxDepreciationEntry.unscoped.get_or_create(
                    tenant=tenant, tax_book=macrs_book, asset=asset,
                    fiscal_year=date.today().year,
                    defaults={
                        'depreciation_amount': (asset.acquisition_cost * Decimal('0.20')).quantize(Decimal('0.01')),
                        'accumulated_depreciation': (asset.acquisition_cost * Decimal('0.20')).quantize(Decimal('0.01')),
                        'recovery_period_years': 5,
                        'convention': 'half_year',
                        'property_class': '5-year property',
                    }
                )

            # --- Physical Inventory ---
            if assets:
                inv, inv_created = PhysicalInventory.unscoped.get_or_create(
                    tenant=tenant, inventory_number=PhysicalInventory.generate_inventory_number(tenant),
                    defaults={
                        'name': f'Annual Inventory Count {date.today().year}',
                        'location': locations[0],
                        'count_date': date.today() - timedelta(days=15),
                        'status': 'reconciled',
                        'conducted_by': users[0],
                    }
                )
                if inv_created:
                    for asset in assets[:5]:
                        PhysicalInventoryItem.objects.get_or_create(
                            inventory=inv, asset=asset,
                            defaults={
                                'expected_location': asset.location,
                                'found_location': asset.location,
                                'is_found': True,
                                'condition': random.choice(['good', 'good', 'good', 'fair']),
                                'scanned_barcode': asset.barcode,
                            }
                        )

        self.stdout.write(
            f'  Created FA data (categories, locations, assets, acquisitions, '
            f'depreciation schedules, transfers, disposals, impairments, tax books, inventories)'
        )

    def _seed_ic_data(self):
        """Seed inventory & cost management sample data."""
        from apps.inventory.models import (
            ItemCategory, UnitOfMeasure, Item, CostLayer, Warehouse,
            PurchaseRequisition, PurchaseRequisitionLine,
            PurchaseOrder, PurchaseOrderLine,
            GoodsReceipt, GoodsReceiptLine,
            InventoryTransaction, InventoryTransfer, InventoryTransferLine,
            COGSCalculation, COGSEntry,
            ReorderSuggestion,
            CycleCountPlan, CycleCountSession, CycleCountItem,
            LandedCostVoucher, LandedCostLine, LandedCostAllocation,
        )
        from apps.general_ledger.models import Account
        from apps.tenants.managers import set_current_tenant

        tenants = Tenant.objects.all()
        if not tenants.exists():
            self.stdout.write('  No tenants found. Skipping IC seeding.')
            return

        for tenant in tenants:
            set_current_tenant(tenant)

            # Get GL accounts for category mapping
            gl_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )[:10])
            if len(gl_accounts) < 3:
                self.stdout.write(f'  Skipping IC for {tenant.name}: not enough GL accounts.')
                continue

            # Get a user
            users = list(CustomUser.objects.all()[:3])
            if not users:
                continue

            # Get vendors (from AP module)
            try:
                from apps.accounts_payable.models import Vendor
                vendors = list(Vendor.unscoped.filter(tenant=tenant)[:5])
            except Exception:
                vendors = []

            # Get fiscal period for COGS
            fiscal_period = FiscalPeriod.unscoped.filter(tenant=tenant).first()

            # =====================================================================
            # Units of Measure
            # =====================================================================
            uom_data = [
                {'code': 'EA', 'name': 'Each', 'abbreviation': 'ea'},
                {'code': 'KG', 'name': 'Kilogram', 'abbreviation': 'kg'},
                {'code': 'LTR', 'name': 'Litre', 'abbreviation': 'L'},
                {'code': 'BOX', 'name': 'Box', 'abbreviation': 'box'},
                {'code': 'PKG', 'name': 'Package', 'abbreviation': 'pkg'},
            ]
            uoms = []
            for ud in uom_data:
                uom, _ = UnitOfMeasure.unscoped.get_or_create(
                    tenant=tenant, code=ud['code'],
                    defaults={'name': ud['name'], 'abbreviation': ud['abbreviation']}
                )
                uoms.append(uom)

            # =====================================================================
            # Item Categories
            # =====================================================================
            categories_data = [
                {'code': 'RAW', 'name': 'Raw Materials'},
                {'code': 'FG', 'name': 'Finished Goods'},
                {'code': 'COMP', 'name': 'Components'},
                {'code': 'PKG', 'name': 'Packaging Materials'},
                {'code': 'MRO', 'name': 'Maintenance & Repair'},
            ]
            categories = []
            for i, cd in enumerate(categories_data):
                cat, _ = ItemCategory.unscoped.get_or_create(
                    tenant=tenant, code=cd['code'],
                    defaults={
                        'name': cd['name'],
                        'gl_inventory_account': gl_accounts[min(i, len(gl_accounts) - 1)],
                        'gl_cogs_account': gl_accounts[min(i + 1, len(gl_accounts) - 1)],
                        'gl_revenue_account': gl_accounts[min(i + 2, len(gl_accounts) - 1)],
                    }
                )
                categories.append(cat)

            # =====================================================================
            # Warehouses
            # =====================================================================
            warehouses_data = [
                {'code': 'WH-MAIN', 'name': 'Main Warehouse', 'address': '100 Warehouse Drive'},
                {'code': 'WH-DIST', 'name': 'Distribution Center', 'address': '200 Logistics Blvd'},
                {'code': 'WH-RET', 'name': 'Returns Warehouse', 'address': '300 Returns Lane'},
            ]
            warehouses = []
            for wd in warehouses_data:
                wh, _ = Warehouse.unscoped.get_or_create(
                    tenant=tenant, code=wd['code'],
                    defaults={'name': wd['name'], 'address': wd['address']}
                )
                warehouses.append(wh)

            # =====================================================================
            # Items
            # =====================================================================
            items_data = [
                {
                    'name': 'Steel Sheet 4x8', 'cat': 0, 'uom': 0, 'type': 'inventory',
                    'costing': 'fifo', 'purchase': Decimal('45.00'), 'selling': Decimal('75.00'),
                    'std_cost': Decimal('45.00'), 'qty': Decimal('250.00'),
                    'reorder_pt': Decimal('50.00'), 'reorder_qty': Decimal('100.00'),
                    'safety': Decimal('25.00'), 'lead': 7,
                },
                {
                    'name': 'Aluminium Rod 10mm', 'cat': 0, 'uom': 1, 'type': 'inventory',
                    'costing': 'fifo', 'purchase': Decimal('12.50'), 'selling': Decimal('22.00'),
                    'std_cost': Decimal('12.50'), 'qty': Decimal('500.00'),
                    'reorder_pt': Decimal('100.00'), 'reorder_qty': Decimal('200.00'),
                    'safety': Decimal('50.00'), 'lead': 5,
                },
                {
                    'name': 'Widget Assembly A1', 'cat': 1, 'uom': 0, 'type': 'inventory',
                    'costing': 'weighted_avg', 'purchase': Decimal('85.00'), 'selling': Decimal('150.00'),
                    'std_cost': Decimal('85.00'), 'qty': Decimal('120.00'),
                    'reorder_pt': Decimal('30.00'), 'reorder_qty': Decimal('50.00'),
                    'safety': Decimal('15.00'), 'lead': 14,
                },
                {
                    'name': 'Circuit Board CB-200', 'cat': 2, 'uom': 0, 'type': 'inventory',
                    'costing': 'standard', 'purchase': Decimal('32.00'), 'selling': Decimal('55.00'),
                    'std_cost': Decimal('32.00'), 'qty': Decimal('800.00'),
                    'reorder_pt': Decimal('150.00'), 'reorder_qty': Decimal('300.00'),
                    'safety': Decimal('75.00'), 'lead': 10,
                },
                {
                    'name': 'Corrugated Box Large', 'cat': 3, 'uom': 3, 'type': 'inventory',
                    'costing': 'weighted_avg', 'purchase': Decimal('2.50'), 'selling': Decimal('0.00'),
                    'std_cost': Decimal('2.50'), 'qty': Decimal('2000.00'),
                    'reorder_pt': Decimal('500.00'), 'reorder_qty': Decimal('1000.00'),
                    'safety': Decimal('250.00'), 'lead': 3,
                },
                {
                    'name': 'Lubricant Oil 5L', 'cat': 4, 'uom': 2, 'type': 'inventory',
                    'costing': 'weighted_avg', 'purchase': Decimal('18.00'), 'selling': Decimal('0.00'),
                    'std_cost': Decimal('18.00'), 'qty': Decimal('60.00'),
                    'reorder_pt': Decimal('15.00'), 'reorder_qty': Decimal('30.00'),
                    'safety': Decimal('10.00'), 'lead': 5,
                },
                {
                    'name': 'Gadget Pro X1', 'cat': 1, 'uom': 0, 'type': 'inventory',
                    'costing': 'fifo', 'purchase': Decimal('120.00'), 'selling': Decimal('220.00'),
                    'std_cost': Decimal('120.00'), 'qty': Decimal('75.00'),
                    'reorder_pt': Decimal('20.00'), 'reorder_qty': Decimal('40.00'),
                    'safety': Decimal('10.00'), 'lead': 21,
                },
                {
                    'name': 'Installation Service', 'cat': 1, 'uom': 0, 'type': 'service',
                    'costing': 'standard', 'purchase': Decimal('0.00'), 'selling': Decimal('200.00'),
                    'std_cost': Decimal('0.00'), 'qty': Decimal('0.00'),
                    'reorder_pt': Decimal('0.00'), 'reorder_qty': Decimal('0.00'),
                    'safety': Decimal('0.00'), 'lead': 0,
                },
            ]
            items = []
            for idx, itd in enumerate(items_data):
                sku = Item.generate_sku(tenant)
                item, created = Item.unscoped.get_or_create(
                    tenant=tenant, name=itd['name'],
                    defaults={
                        'sku': sku,
                        'category': categories[itd['cat']],
                        'base_uom': uoms[itd['uom']],
                        'item_type': itd['type'],
                        'costing_method': itd['costing'],
                        'standard_cost': itd['std_cost'],
                        'purchase_price': itd['purchase'],
                        'selling_price': itd['selling'],
                        'quantity_on_hand': itd['qty'],
                        'weighted_avg_cost': itd['purchase'] if itd['costing'] == 'weighted_avg' else Decimal('0.00'),
                        'reorder_point': itd['reorder_pt'],
                        'reorder_quantity': itd['reorder_qty'],
                        'safety_stock': itd['safety'],
                        'lead_time_days': itd['lead'],
                        'weight': Decimal(str(random.uniform(0.5, 25.0))).quantize(Decimal('0.0001')) if itd['type'] == 'inventory' else None,
                    }
                )
                items.append(item)

            # =====================================================================
            # Cost Layers (for FIFO/LIFO items)
            # =====================================================================
            for item in items:
                if item.item_type != 'inventory' or item.quantity_on_hand <= 0:
                    continue
                # Create 2-3 cost layers per item to simulate multiple receipts
                remaining = item.quantity_on_hand
                layer_count = random.randint(2, 3)
                for layer_idx in range(layer_count):
                    if layer_idx == layer_count - 1:
                        layer_qty = remaining
                    else:
                        layer_qty = (remaining * Decimal(str(random.uniform(0.3, 0.5)))).quantize(Decimal('0.01'))
                    remaining -= layer_qty
                    if layer_qty <= 0:
                        continue
                    # Vary cost slightly per layer
                    cost_variation = Decimal(str(random.uniform(0.90, 1.10))).quantize(Decimal('0.0001'))
                    unit_cost = (item.purchase_price * cost_variation).quantize(Decimal('0.0001'))
                    receipt_date = date.today() - timedelta(days=random.randint(30, 180))
                    CostLayer.unscoped.get_or_create(
                        tenant=tenant, item=item, receipt_date=receipt_date,
                        original_quantity=layer_qty,
                        defaults={
                            'quantity_on_hand': layer_qty,
                            'unit_cost': unit_cost,
                            'source_type': 'purchase',
                            'source_reference': f'Opening-{item.sku}-L{layer_idx + 1}',
                        }
                    )

            # =====================================================================
            # Purchase Requisition
            # =====================================================================
            req_num = PurchaseRequisition.generate_requisition_number(tenant)
            requisition, req_created = PurchaseRequisition.unscoped.get_or_create(
                tenant=tenant, requisition_number=req_num,
                defaults={
                    'date': date.today() - timedelta(days=25),
                    'requested_by': users[0],
                    'status': 'approved',
                    'notes': 'Monthly replenishment requisition for raw materials.',
                }
            )
            if req_created and len(items) >= 2:
                PurchaseRequisitionLine.objects.create(
                    requisition=requisition, item=items[0],
                    quantity=Decimal('100.00'), uom=uoms[0],
                    estimated_unit_price=items[0].purchase_price,
                )
                PurchaseRequisitionLine.objects.create(
                    requisition=requisition, item=items[1],
                    quantity=Decimal('200.00'), uom=uoms[1],
                    estimated_unit_price=items[1].purchase_price,
                )

            # =====================================================================
            # Purchase Orders (2 POs)
            # =====================================================================
            pos = []
            for po_idx in range(2):
                po_num = PurchaseOrder.generate_po_number(tenant)
                vendor = vendors[po_idx % len(vendors)] if vendors else None
                if not vendor:
                    break
                po_date = date.today() - timedelta(days=20 - (po_idx * 10))
                po_status = 'received' if po_idx == 0 else 'approved'
                po, po_created = PurchaseOrder.unscoped.get_or_create(
                    tenant=tenant, po_number=po_num,
                    defaults={
                        'vendor': vendor,
                        'requisition': requisition if po_idx == 0 else None,
                        'date': po_date,
                        'expected_delivery': po_date + timedelta(days=14),
                        'status': po_status,
                        'total_amount': Decimal('0.00'),
                        'created_by': users[0],
                        'approved_by': users[1] if len(users) > 1 else users[0],
                    }
                )
                if po_created:
                    total = Decimal('0.00')
                    # Add 2-3 lines per PO
                    po_items = items[po_idx * 2: po_idx * 2 + 3] if len(items) > po_idx * 2 + 2 else items[:3]
                    for pi in po_items:
                        if pi.item_type == 'service':
                            continue
                        qty = Decimal(str(random.randint(50, 200)))
                        line = PurchaseOrderLine.objects.create(
                            purchase_order=po, item=pi,
                            quantity=qty, unit_price=pi.purchase_price,
                            uom=pi.base_uom,
                            received_quantity=qty if po_status == 'received' else Decimal('0.00'),
                        )
                        total += line.line_total
                    po.total_amount = total
                    po.save()
                pos.append(po)

            # =====================================================================
            # Goods Receipt (for the first PO)
            # =====================================================================
            receipt = None
            if pos:
                grn_num = GoodsReceipt.generate_receipt_number(tenant)
                receipt, grn_created = GoodsReceipt.unscoped.get_or_create(
                    tenant=tenant, receipt_number=grn_num,
                    defaults={
                        'purchase_order': pos[0],
                        'receipt_date': date.today() - timedelta(days=15),
                        'received_by': users[0],
                        'warehouse': warehouses[0],
                        'status': 'posted',
                        'notes': 'All items received in good condition.',
                    }
                )
                if grn_created:
                    for po_line in pos[0].lines.all():
                        GoodsReceiptLine.objects.create(
                            goods_receipt=receipt,
                            po_line=po_line,
                            item=po_line.item,
                            quantity_received=po_line.quantity,
                            unit_cost=po_line.unit_price,
                        )

            # =====================================================================
            # Inventory Transactions (adjustment + scrap)
            # =====================================================================
            if items:
                # Positive adjustment
                adj_num = InventoryTransaction.generate_transaction_number(tenant)
                InventoryTransaction.unscoped.get_or_create(
                    tenant=tenant, transaction_number=adj_num,
                    defaults={
                        'date': date.today() - timedelta(days=10),
                        'item': items[0],
                        'transaction_type': 'adjustment',
                        'quantity': Decimal('25.00'),
                        'unit_cost': items[0].purchase_price,
                        'warehouse': warehouses[0],
                        'reference': 'ADJ-opening-balance-correction',
                        'notes': 'Opening balance correction after physical count.',
                        'posted_by': users[0],
                    }
                )

                # Scrap transaction
                scrap_num = InventoryTransaction.generate_transaction_number(tenant)
                InventoryTransaction.unscoped.get_or_create(
                    tenant=tenant, transaction_number=scrap_num,
                    defaults={
                        'date': date.today() - timedelta(days=5),
                        'item': items[3] if len(items) > 3 else items[0],
                        'transaction_type': 'scrap',
                        'quantity': Decimal('-10.00'),
                        'unit_cost': items[3].purchase_price if len(items) > 3 else items[0].purchase_price,
                        'warehouse': warehouses[0],
                        'reference': 'SCRAP-damaged-goods',
                        'notes': 'Damaged during handling — scrapped per QC inspection.',
                        'posted_by': users[0],
                    }
                )

            # =====================================================================
            # Inventory Transfer
            # =====================================================================
            if len(items) >= 3 and len(warehouses) >= 2:
                trf_num = InventoryTransfer.generate_transfer_number(tenant)
                transfer, trf_created = InventoryTransfer.unscoped.get_or_create(
                    tenant=tenant, transfer_number=trf_num,
                    defaults={
                        'date': date.today() - timedelta(days=8),
                        'from_warehouse': warehouses[0],
                        'to_warehouse': warehouses[1],
                        'status': 'completed',
                        'created_by': users[0],
                        'notes': 'Replenishment transfer to distribution center.',
                    }
                )
                if trf_created:
                    InventoryTransferLine.objects.create(
                        transfer=transfer, item=items[2],
                        quantity=Decimal('20.00'),
                        unit_cost=items[2].purchase_price,
                    )
                    InventoryTransferLine.objects.create(
                        transfer=transfer, item=items[4],
                        quantity=Decimal('100.00'),
                        unit_cost=items[4].purchase_price,
                    )

            # =====================================================================
            # COGS Calculation
            # =====================================================================
            if fiscal_period and items:
                cogs_num = COGSCalculation.generate_calculation_number(tenant)
                cogs_calc, cogs_created = COGSCalculation.unscoped.get_or_create(
                    tenant=tenant, calculation_number=cogs_num,
                    defaults={
                        'period': fiscal_period,
                        'calculation_date': date.today() - timedelta(days=3),
                        'method': 'weighted_avg',
                        'status': 'draft',
                        'total_cogs': Decimal('0.00'),
                        'created_by': users[0],
                        'notes': 'Monthly COGS calculation.',
                    }
                )
                if cogs_created:
                    total_cogs = Decimal('0.00')
                    for item in items[:5]:
                        if item.item_type != 'inventory':
                            continue
                        qty_sold = Decimal(str(random.randint(10, 50)))
                        unit_cost = item.weighted_avg_cost if item.weighted_avg_cost > 0 else item.standard_cost
                        if unit_cost <= 0:
                            unit_cost = item.purchase_price
                        entry_total = (qty_sold * unit_cost).quantize(Decimal('0.01'))
                        COGSEntry.objects.create(
                            calculation=cogs_calc, item=item,
                            quantity_sold=qty_sold, unit_cost=unit_cost,
                            total_cost=entry_total,
                        )
                        total_cogs += entry_total
                    cogs_calc.total_cogs = total_cogs
                    cogs_calc.save()

            # =====================================================================
            # Reorder Suggestions
            # =====================================================================
            reorder_statuses = ['pending', 'pending', 'pending', 'approved', 'approved', 'ordered', 'dismissed']
            inv_items = [i for i in items if i.item_type == 'inventory' and i.reorder_point > 0]
            for idx, item in enumerate(inv_items):
                status = reorder_statuses[idx % len(reorder_statuses)]
                low_stock = max(Decimal('0'), item.reorder_point - Decimal(str(random.randint(5, 30))))
                ReorderSuggestion.unscoped.get_or_create(
                    tenant=tenant, item=item, status=status,
                    defaults={
                        'current_stock': low_stock,
                        'reorder_point': item.reorder_point,
                        'suggested_quantity': item.reorder_quantity,
                        'vendor': vendors[idx % len(vendors)] if vendors else None,
                    }
                )

            # =====================================================================
            # Cycle Count Plan + Session
            # =====================================================================
            plan_num = CycleCountPlan.generate_plan_number(tenant)
            plan, plan_created = CycleCountPlan.unscoped.get_or_create(
                tenant=tenant, plan_number=plan_num,
                defaults={
                    'name': 'Monthly Full Count',
                    'frequency': 'monthly',
                    'item_selection_method': 'all',
                    'warehouse': warehouses[0],
                    'status': 'active',
                    'next_count_date': date.today() + timedelta(days=30),
                }
            )

            session_num = CycleCountSession.generate_session_number(tenant)
            session, sess_created = CycleCountSession.unscoped.get_or_create(
                tenant=tenant, session_number=session_num,
                defaults={
                    'plan': plan,
                    'count_date': date.today() - timedelta(days=2),
                    'counted_by': users[0],
                    'warehouse': warehouses[0],
                    'status': 'completed',
                    'notes': 'Routine monthly cycle count.',
                }
            )
            if sess_created:
                for item in items[:5]:
                    if item.item_type != 'inventory':
                        continue
                    # Simulate slight variance
                    variance = Decimal(str(random.choice([-3, -2, -1, 0, 0, 0, 1, 2])))
                    counted = item.quantity_on_hand + variance
                    CycleCountItem.objects.create(
                        session=session, item=item,
                        system_quantity=item.quantity_on_hand,
                        counted_quantity=counted,
                        status='counted',
                    )

            # =====================================================================
            # Landed Cost Voucher
            # =====================================================================
            if receipt and receipt.status == 'posted':
                lcv_num = LandedCostVoucher.generate_voucher_number(tenant)
                voucher, lcv_created = LandedCostVoucher.unscoped.get_or_create(
                    tenant=tenant, voucher_number=lcv_num,
                    defaults={
                        'goods_receipt': receipt,
                        'date': date.today() - timedelta(days=12),
                        'status': 'draft',
                        'total_additional_cost': Decimal('1250.00'),
                        'created_by': users[0],
                        'notes': 'Freight and customs charges for shipment.',
                    }
                )
                if lcv_created:
                    LandedCostLine.objects.create(
                        voucher=voucher, cost_type='freight',
                        description='Ocean freight charges',
                        amount=Decimal('850.00'),
                        vendor=vendors[1] if len(vendors) > 1 else None,
                    )
                    LandedCostLine.objects.create(
                        voucher=voucher, cost_type='duty',
                        description='Import customs duty',
                        amount=Decimal('300.00'),
                    )
                    LandedCostLine.objects.create(
                        voucher=voucher, cost_type='handling',
                        description='Port handling charges',
                        amount=Decimal('100.00'),
                    )

                    # Allocations
                    receipt_lines = list(receipt.lines.all())
                    if receipt_lines:
                        total_value = sum(rl.quantity_received * rl.unit_cost for rl in receipt_lines)
                        for rl in receipt_lines:
                            line_value = rl.quantity_received * rl.unit_cost
                            proportion = line_value / total_value if total_value else Decimal('0')
                            alloc_amount = (Decimal('1250.00') * proportion).quantize(Decimal('0.01'))
                            LandedCostAllocation.objects.create(
                                voucher=voucher, item=rl.item,
                                goods_receipt_line=rl,
                                allocated_amount=alloc_amount,
                                allocation_method='by_value',
                            )

        self.stdout.write(
            f'  Created IC data (categories, UoMs, items, warehouses, cost layers, '
            f'requisitions, POs, receipts, transactions, transfers, COGS, '
            f'reorder suggestions, cycle counts, landed cost vouchers)'
        )

    # =================================================================
    # PAYROLL INTEGRATION
    # =================================================================

    def _seed_pr_data(self):
        """Seed payroll integration sample data."""
        from apps.payroll.models import (
            Employee, PayrollJournal, PayrollJournalLine,
            TaxWithholding, TaxRemittance,
            BenefitPlan, EmployeeBenefit,
            Garnishment,
            WorkersCompClass, WorkersCompAssignment,
            PayrollReconciliation,
        )
        from apps.general_ledger.models import Account
        from apps.tenants.managers import set_current_tenant

        tenants = Tenant.objects.all()
        if not tenants.exists():
            self.stdout.write('  No tenants found. Skipping PR seeding.')
            return

        for tenant in tenants:
            set_current_tenant(tenant)

            # Get GL accounts — need expense and liability accounts
            expense_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['EXP', 'EXPENSE', 'OE']
            )[:10])
            liability_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['CL', 'LIA', 'LIABILITY', 'NCL']
            )[:5])

            # Fallback: use any non-header accounts
            all_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )[:15])
            if len(expense_accounts) < 3:
                expense_accounts = all_accounts[:8]
            if len(liability_accounts) < 2:
                liability_accounts = all_accounts[8:12] if len(all_accounts) > 8 else all_accounts[:4]

            if len(expense_accounts) < 2 or len(liability_accounts) < 1:
                self.stdout.write(f'  Skipping PR for {tenant.name}: not enough GL accounts.')
                continue

            users = list(CustomUser.objects.all()[:3])
            if not users:
                continue

            fiscal_period = FiscalPeriod.unscoped.filter(tenant=tenant).first()

            # =============================================================
            # 1. Employees
            # =============================================================
            employees_data = [
                {
                    'first_name': 'John', 'last_name': 'Martinez',
                    'email': 'john.martinez@company.com', 'phone': '555-0101',
                    'department': 'Engineering', 'position': 'Senior Developer',
                    'pay_type': 'salary', 'pay_rate': Decimal('95000.00'),
                    'pay_frequency': 'biweekly', 'filing_status': 'married',
                    'federal_allowances': 3, 'state_allowances': 2,
                    'hire_days_ago': 730,
                },
                {
                    'first_name': 'Sarah', 'last_name': 'Chen',
                    'email': 'sarah.chen@company.com', 'phone': '555-0102',
                    'department': 'Finance', 'position': 'Controller',
                    'pay_type': 'salary', 'pay_rate': Decimal('110000.00'),
                    'pay_frequency': 'semimonthly', 'filing_status': 'single',
                    'federal_allowances': 1, 'state_allowances': 1,
                    'hire_days_ago': 1095,
                },
                {
                    'first_name': 'Michael', 'last_name': 'Johnson',
                    'email': 'michael.johnson@company.com', 'phone': '555-0103',
                    'department': 'Operations', 'position': 'Warehouse Manager',
                    'pay_type': 'salary', 'pay_rate': Decimal('72000.00'),
                    'pay_frequency': 'biweekly', 'filing_status': 'married',
                    'federal_allowances': 4, 'state_allowances': 3,
                    'hire_days_ago': 1460,
                },
                {
                    'first_name': 'Emily', 'last_name': 'Davis',
                    'email': 'emily.davis@company.com', 'phone': '555-0104',
                    'department': 'Operations', 'position': 'Production Worker',
                    'pay_type': 'hourly', 'pay_rate': Decimal('28.50'),
                    'pay_frequency': 'weekly', 'filing_status': 'single',
                    'federal_allowances': 1, 'state_allowances': 1,
                    'hire_days_ago': 365,
                },
                {
                    'first_name': 'Robert', 'last_name': 'Wilson',
                    'email': 'robert.wilson@company.com', 'phone': '555-0105',
                    'department': 'Sales', 'position': 'Sales Representative',
                    'pay_type': 'salary', 'pay_rate': Decimal('65000.00'),
                    'pay_frequency': 'biweekly', 'filing_status': 'head_of_household',
                    'federal_allowances': 2, 'state_allowances': 2,
                    'hire_days_ago': 545,
                },
                {
                    'first_name': 'Lisa', 'last_name': 'Anderson',
                    'email': 'lisa.anderson@company.com', 'phone': '555-0106',
                    'department': 'Engineering', 'position': 'QA Engineer',
                    'pay_type': 'salary', 'pay_rate': Decimal('82000.00'),
                    'pay_frequency': 'biweekly', 'filing_status': 'married',
                    'federal_allowances': 2, 'state_allowances': 2,
                    'hire_days_ago': 900,
                },
                {
                    'first_name': 'David', 'last_name': 'Brown',
                    'email': 'david.brown@company.com', 'phone': '555-0107',
                    'department': 'Operations', 'position': 'Maintenance Technician',
                    'pay_type': 'hourly', 'pay_rate': Decimal('32.00'),
                    'pay_frequency': 'weekly', 'filing_status': 'married',
                    'federal_allowances': 3, 'state_allowances': 2,
                    'hire_days_ago': 1200,
                },
                {
                    'first_name': 'Jennifer', 'last_name': 'Taylor',
                    'email': 'jennifer.taylor@company.com', 'phone': '555-0108',
                    'department': 'HR', 'position': 'HR Manager',
                    'pay_type': 'salary', 'pay_rate': Decimal('88000.00'),
                    'pay_frequency': 'semimonthly', 'filing_status': 'single',
                    'federal_allowances': 1, 'state_allowances': 1,
                    'hire_days_ago': 600,
                },
            ]

            employees = []
            for ed in employees_data:
                emp, _ = Employee.unscoped.get_or_create(
                    tenant=tenant, email=ed['email'],
                    defaults={
                        'employee_number': Employee.generate_employee_number(tenant),
                        'first_name': ed['first_name'],
                        'last_name': ed['last_name'],
                        'phone': ed['phone'],
                        'department': ed['department'],
                        'position': ed['position'],
                        'hire_date': date.today() - timedelta(days=ed['hire_days_ago']),
                        'pay_type': ed['pay_type'],
                        'pay_rate': ed['pay_rate'],
                        'pay_frequency': ed['pay_frequency'],
                        'filing_status': ed['filing_status'],
                        'federal_allowances': ed['federal_allowances'],
                        'state_allowances': ed['state_allowances'],
                        'gl_expense_account': expense_accounts[len(employees) % len(expense_accounts)],
                        'is_active': True,
                    }
                )
                employees.append(emp)

            # =============================================================
            # 2. Tax Withholdings (per employee)
            # =============================================================
            tax_configs = [
                {'tax_type': 'federal', 'rate': Decimal('22.0000'), 'annual_limit': None, 'is_employer_paid': False},
                {'tax_type': 'state', 'rate': Decimal('5.7500'), 'annual_limit': None, 'is_employer_paid': False},
                {'tax_type': 'social_security', 'rate': Decimal('6.2000'), 'annual_limit': Decimal('168600.00'), 'is_employer_paid': False},
                {'tax_type': 'medicare', 'rate': Decimal('1.4500'), 'annual_limit': None, 'is_employer_paid': False},
                {'tax_type': 'futa', 'rate': Decimal('6.0000'), 'annual_limit': Decimal('7000.00'), 'is_employer_paid': True},
                {'tax_type': 'suta', 'rate': Decimal('3.4000'), 'annual_limit': Decimal('35000.00'), 'is_employer_paid': True},
            ]

            for emp in employees:
                for tc in tax_configs:
                    TaxWithholding.unscoped.get_or_create(
                        tenant=tenant, employee=emp, tax_type=tc['tax_type'],
                        effective_date=emp.hire_date,
                        defaults={
                            'rate': tc['rate'],
                            'ytd_amount': (emp.pay_rate * tc['rate'] / Decimal('100') * Decimal('0.15')).quantize(Decimal('0.01')),
                            'annual_limit': tc['annual_limit'],
                            'is_employer_paid': tc['is_employer_paid'],
                        }
                    )

            # =============================================================
            # 3. Benefit Plans
            # =============================================================
            benefit_plans_data = [
                {
                    'code': 'HEALTH-PPO', 'name': 'Health Insurance - PPO Plan',
                    'benefit_type': 'health_insurance',
                    'employer_contribution_type': 'fixed',
                    'employer_contribution_amount': Decimal('450.00'),
                    'employer_match_limit': None,
                },
                {
                    'code': 'DENTAL-STD', 'name': 'Dental Insurance - Standard',
                    'benefit_type': 'dental',
                    'employer_contribution_type': 'fixed',
                    'employer_contribution_amount': Decimal('75.00'),
                    'employer_match_limit': None,
                },
                {
                    'code': 'VISION-BAS', 'name': 'Vision Insurance - Basic',
                    'benefit_type': 'vision',
                    'employer_contribution_type': 'fixed',
                    'employer_contribution_amount': Decimal('25.00'),
                    'employer_match_limit': None,
                },
                {
                    'code': '401K-MATCH', 'name': '401(k) Retirement Plan',
                    'benefit_type': '401k',
                    'employer_contribution_type': 'match',
                    'employer_contribution_amount': Decimal('50.00'),
                    'employer_match_limit': Decimal('500.00'),
                },
                {
                    'code': 'LIFE-BASIC', 'name': 'Basic Life Insurance',
                    'benefit_type': 'life',
                    'employer_contribution_type': 'fixed',
                    'employer_contribution_amount': Decimal('35.00'),
                    'employer_match_limit': None,
                },
                {
                    'code': 'HSA-PLAN', 'name': 'Health Savings Account',
                    'benefit_type': 'hsa',
                    'employer_contribution_type': 'fixed',
                    'employer_contribution_amount': Decimal('100.00'),
                    'employer_match_limit': None,
                },
            ]

            benefit_plans = []
            for i, bp in enumerate(benefit_plans_data):
                plan, _ = BenefitPlan.unscoped.get_or_create(
                    tenant=tenant, code=bp['code'],
                    defaults={
                        'name': bp['name'],
                        'benefit_type': bp['benefit_type'],
                        'employer_contribution_type': bp['employer_contribution_type'],
                        'employer_contribution_amount': bp['employer_contribution_amount'],
                        'employer_match_limit': bp['employer_match_limit'],
                        'gl_expense_account': expense_accounts[min(i, len(expense_accounts) - 1)],
                        'gl_liability_account': liability_accounts[min(i, len(liability_accounts) - 1)],
                        'is_active': True,
                    }
                )
                benefit_plans.append(plan)

            # =============================================================
            # 4. Employee Benefit Enrollments
            # =============================================================
            enrollment_map = {
                0: [0, 1, 2, 3, 4, 5],     # John - all plans
                1: [0, 1, 3, 4],            # Sarah - health, dental, 401k, life
                2: [0, 1, 2, 3, 4],         # Michael - all except HSA
                3: [0, 1, 4],               # Emily - health, dental, life
                4: [0, 3, 4],               # Robert - health, 401k, life
                5: [0, 1, 2, 3, 4, 5],     # Lisa - all plans
                6: [0, 1, 4],               # David - health, dental, life
                7: [0, 1, 3, 4, 5],         # Jennifer - health, dental, 401k, life, hsa
            }

            employee_contributions = {
                'HEALTH-PPO': Decimal('150.00'),
                'DENTAL-STD': Decimal('25.00'),
                'VISION-BAS': Decimal('10.00'),
                '401K-MATCH': Decimal('350.00'),
                'LIFE-BASIC': Decimal('0.00'),
                'HSA-PLAN': Decimal('75.00'),
            }

            for emp_idx, plan_indices in enrollment_map.items():
                if emp_idx >= len(employees):
                    continue
                emp = employees[emp_idx]
                for plan_idx in plan_indices:
                    if plan_idx >= len(benefit_plans):
                        continue
                    plan = benefit_plans[plan_idx]
                    EmployeeBenefit.objects.get_or_create(
                        employee=emp, benefit_plan=plan,
                        defaults={
                            'employee_contribution': employee_contributions.get(plan.code, Decimal('0.00')),
                            'enrollment_date': emp.hire_date + timedelta(days=30),
                            'is_active': True,
                        }
                    )

            # =============================================================
            # 5. Garnishments
            # =============================================================
            garnishments_data = [
                {
                    'employee_idx': 2,  # Michael Johnson
                    'garnishment_type': 'child_support',
                    'case_number': 'CS-2024-04512',
                    'description': 'Monthly child support per court order',
                    'amount': Decimal('650.00'),
                    'is_percentage': False,
                    'max_percentage': Decimal('50.00'),
                    'priority': 1,
                    'total_required': Decimal('0.00'),
                    'total_paid': Decimal('7800.00'),
                    'status': 'active',
                    'issuing_authority': 'County Family Court',
                },
                {
                    'employee_idx': 4,  # Robert Wilson
                    'garnishment_type': 'student_loan',
                    'case_number': 'SL-2023-88741',
                    'description': 'Federal student loan wage garnishment',
                    'amount': Decimal('15.00'),
                    'is_percentage': True,
                    'max_percentage': Decimal('15.00'),
                    'priority': 2,
                    'total_required': Decimal('35000.00'),
                    'total_paid': Decimal('4875.00'),
                    'status': 'active',
                    'issuing_authority': 'US Department of Education',
                },
                {
                    'employee_idx': 6,  # David Brown
                    'garnishment_type': 'tax_levy',
                    'case_number': 'TL-2025-00198',
                    'description': 'IRS tax levy for unpaid 2022 taxes',
                    'amount': Decimal('500.00'),
                    'is_percentage': False,
                    'max_percentage': Decimal('25.00'),
                    'priority': 1,
                    'total_required': Decimal('8500.00'),
                    'total_paid': Decimal('3000.00'),
                    'status': 'active',
                    'issuing_authority': 'Internal Revenue Service',
                },
            ]

            for gd in garnishments_data:
                if gd['employee_idx'] >= len(employees):
                    continue
                emp = employees[gd['employee_idx']]
                Garnishment.unscoped.get_or_create(
                    tenant=tenant, employee=emp, case_number=gd['case_number'],
                    defaults={
                        'garnishment_type': gd['garnishment_type'],
                        'description': gd['description'],
                        'amount': gd['amount'],
                        'is_percentage': gd['is_percentage'],
                        'max_percentage': gd['max_percentage'],
                        'priority': gd['priority'],
                        'start_date': date.today() - timedelta(days=180),
                        'total_required': gd['total_required'],
                        'total_paid': gd['total_paid'],
                        'status': gd['status'],
                        'issuing_authority': gd['issuing_authority'],
                    }
                )

            # =============================================================
            # 6. Workers Comp Classes
            # =============================================================
            comp_classes_data = [
                {
                    'code': 'WC-8810', 'name': 'Clerical Office Employees',
                    'description': 'Standard office and clerical work',
                    'rate': Decimal('0.3500'),
                },
                {
                    'code': 'WC-8742', 'name': 'Sales Outside',
                    'description': 'Outside sales representatives',
                    'rate': Decimal('0.5200'),
                },
                {
                    'code': 'WC-3632', 'name': 'Machine Shop',
                    'description': 'Machine shop and manufacturing operations',
                    'rate': Decimal('3.7500'),
                },
                {
                    'code': 'WC-7380', 'name': 'Drivers',
                    'description': 'Delivery and transport drivers',
                    'rate': Decimal('5.2000'),
                },
                {
                    'code': 'WC-5606', 'name': 'Contractors - Executive',
                    'description': 'Executive supervisors for construction/contractors',
                    'rate': Decimal('2.1000'),
                },
            ]

            comp_classes = []
            for i, cc in enumerate(comp_classes_data):
                comp_cls, _ = WorkersCompClass.unscoped.get_or_create(
                    tenant=tenant, code=cc['code'],
                    defaults={
                        'name': cc['name'],
                        'description': cc['description'],
                        'rate': cc['rate'],
                        'effective_date': date(date.today().year, 1, 1),
                        'gl_expense_account': expense_accounts[min(i, len(expense_accounts) - 1)],
                        'is_active': True,
                    }
                )
                comp_classes.append(comp_cls)

            # =============================================================
            # 7. Workers Comp Assignments
            # =============================================================
            # Map: employee index -> comp class index
            wc_assignments = {
                0: 0,   # John (Engineering) -> Clerical
                1: 0,   # Sarah (Finance) -> Clerical
                2: 2,   # Michael (Operations/Warehouse) -> Machine Shop
                3: 2,   # Emily (Operations/Production) -> Machine Shop
                4: 1,   # Robert (Sales) -> Sales Outside
                5: 0,   # Lisa (Engineering) -> Clerical
                6: 2,   # David (Operations/Maintenance) -> Machine Shop
                7: 0,   # Jennifer (HR) -> Clerical
            }

            for emp_idx, cc_idx in wc_assignments.items():
                if emp_idx >= len(employees) or cc_idx >= len(comp_classes):
                    continue
                WorkersCompAssignment.objects.get_or_create(
                    employee=employees[emp_idx],
                    comp_class=comp_classes[cc_idx],
                    effective_date=employees[emp_idx].hire_date,
                )

            # =============================================================
            # 8. Payroll Journals (3 pay runs)
            # =============================================================
            journals = []
            payroll_runs = [
                {
                    'days_ago_start': 42, 'days_ago_end': 29, 'days_ago_pay': 26,
                    'status': 'posted',
                },
                {
                    'days_ago_start': 28, 'days_ago_end': 15, 'days_ago_pay': 12,
                    'status': 'posted',
                },
                {
                    'days_ago_start': 14, 'days_ago_end': 1, 'days_ago_pay': 0,
                    'status': 'calculated',
                },
            ]

            for pr_data in payroll_runs:
                jnum = PayrollJournal.generate_journal_number(tenant)
                journal, j_created = PayrollJournal.unscoped.get_or_create(
                    tenant=tenant, journal_number=jnum,
                    defaults={
                        'pay_period_start': date.today() - timedelta(days=pr_data['days_ago_start']),
                        'pay_period_end': date.today() - timedelta(days=pr_data['days_ago_end']),
                        'pay_date': date.today() - timedelta(days=pr_data['days_ago_pay']),
                        'status': pr_data['status'],
                        'fiscal_period': fiscal_period,
                        'created_by': users[0],
                        'notes': f'Bi-weekly payroll run',
                    }
                )
                journals.append((journal, j_created))

            # =============================================================
            # 9. Payroll Journal Lines (employee pay details)
            # =============================================================
            for journal, j_created in journals:
                if not j_created:
                    continue

                total_gross = Decimal('0.00')
                total_deductions = Decimal('0.00')
                total_net = Decimal('0.00')

                for emp in employees:
                    # Calculate gross pay
                    if emp.pay_type == 'hourly':
                        regular_hours = Decimal('80.00')  # 2-week period
                        overtime_hours = Decimal(str(random.choice([0, 0, 4, 6, 8])))
                        gross = regular_hours * emp.pay_rate
                        ot_pay = overtime_hours * emp.pay_rate * Decimal('1.50')
                    else:
                        regular_hours = Decimal('80.00')
                        overtime_hours = Decimal('0.00')
                        if emp.pay_frequency == 'biweekly':
                            gross = (emp.pay_rate / Decimal('26')).quantize(Decimal('0.01'))
                        elif emp.pay_frequency == 'semimonthly':
                            gross = (emp.pay_rate / Decimal('24')).quantize(Decimal('0.01'))
                        elif emp.pay_frequency == 'weekly':
                            gross = (emp.pay_rate / Decimal('52')).quantize(Decimal('0.01'))
                        else:
                            gross = (emp.pay_rate / Decimal('12')).quantize(Decimal('0.01'))
                        ot_pay = Decimal('0.00')

                    total_gross_pay = gross + ot_pay

                    # Tax calculations
                    fed_tax = (total_gross_pay * Decimal('0.22')).quantize(Decimal('0.01'))
                    state_tax = (total_gross_pay * Decimal('0.0575')).quantize(Decimal('0.01'))
                    local_tax = (total_gross_pay * Decimal('0.01')).quantize(Decimal('0.01'))
                    ss_tax = (total_gross_pay * Decimal('0.062')).quantize(Decimal('0.01'))
                    med_tax = (total_gross_pay * Decimal('0.0145')).quantize(Decimal('0.01'))

                    # Benefits deductions (from employee contribution)
                    benefits_ded = Decimal('0.00')
                    for eb in EmployeeBenefit.objects.filter(employee=emp, is_active=True):
                        benefits_ded += eb.employee_contribution

                    # Garnishment deductions
                    garn_ded = Decimal('0.00')
                    for g in Garnishment.unscoped.filter(tenant=tenant, employee=emp, status='active'):
                        if g.is_percentage:
                            garn_ded += (total_gross_pay * g.amount / Decimal('100')).quantize(Decimal('0.01'))
                        else:
                            garn_ded += g.amount

                    total_ded = fed_tax + state_tax + local_tax + ss_tax + med_tax + benefits_ded + garn_ded
                    net = total_gross_pay - total_ded

                    PayrollJournalLine.objects.create(
                        payroll_journal=journal,
                        employee=emp,
                        regular_hours=regular_hours,
                        overtime_hours=overtime_hours,
                        gross_pay=total_gross_pay,
                        overtime_pay=ot_pay,
                        federal_tax=fed_tax,
                        state_tax=state_tax,
                        local_tax=local_tax,
                        social_security=ss_tax,
                        medicare=med_tax,
                        benefits_deduction=benefits_ded,
                        garnishment_deduction=garn_ded,
                        other_deductions=Decimal('0.00'),
                        total_deductions=total_ded,
                        net_pay=net,
                    )

                    total_gross += total_gross_pay
                    total_deductions += total_ded
                    total_net += net

                # Update journal totals
                journal.total_gross = total_gross
                journal.total_deductions = total_deductions
                journal.total_net = total_net
                journal.save()

            # =============================================================
            # 10. Tax Remittances
            # =============================================================
            remittance_data = [
                {
                    'tax_type': 'federal',
                    'period_start_ago': 60, 'period_end_ago': 31,
                    'amount': Decimal('12500.00'),
                    'status': 'paid', 'days_ago_due': 15, 'paid': True,
                },
                {
                    'tax_type': 'state',
                    'period_start_ago': 60, 'period_end_ago': 31,
                    'amount': Decimal('3250.00'),
                    'status': 'paid', 'days_ago_due': 15, 'paid': True,
                },
                {
                    'tax_type': 'social_security',
                    'period_start_ago': 60, 'period_end_ago': 31,
                    'amount': Decimal('5100.00'),
                    'status': 'paid', 'days_ago_due': 15, 'paid': True,
                },
                {
                    'tax_type': 'federal',
                    'period_start_ago': 30, 'period_end_ago': 1,
                    'amount': Decimal('13200.00'),
                    'status': 'pending', 'days_ago_due': -10, 'paid': False,
                },
                {
                    'tax_type': 'state',
                    'period_start_ago': 30, 'period_end_ago': 1,
                    'amount': Decimal('3400.00'),
                    'status': 'pending', 'days_ago_due': -10, 'paid': False,
                },
                {
                    'tax_type': 'futa',
                    'period_start_ago': 90, 'period_end_ago': 1,
                    'amount': Decimal('1680.00'),
                    'status': 'overdue', 'days_ago_due': 5, 'paid': False,
                },
            ]

            for rd in remittance_data:
                rnum = TaxRemittance.generate_remittance_number(tenant)
                TaxRemittance.unscoped.get_or_create(
                    tenant=tenant, remittance_number=rnum,
                    defaults={
                        'tax_type': rd['tax_type'],
                        'period_start': date.today() - timedelta(days=rd['period_start_ago']),
                        'period_end': date.today() - timedelta(days=rd['period_end_ago']),
                        'amount_due': rd['amount'],
                        'amount_paid': rd['amount'] if rd['paid'] else Decimal('0.00'),
                        'due_date': date.today() - timedelta(days=rd['days_ago_due']),
                        'paid_date': (date.today() - timedelta(days=rd['days_ago_due'] + 2)) if rd['paid'] else None,
                        'status': rd['status'],
                    }
                )

            # =============================================================
            # 11. Payroll Reconciliations (for posted journals)
            # =============================================================
            for journal, j_created in journals:
                if journal.status != 'posted':
                    continue

                lines = journal.lines.all()
                t_gross = sum(l.gross_pay for l in lines)
                t_taxes = sum(
                    l.federal_tax + l.state_tax + l.local_tax + l.social_security + l.medicare
                    for l in lines
                )
                t_benefits = sum(l.benefits_deduction for l in lines)
                t_garnishments = sum(l.garnishment_deduction for l in lines)
                t_net = sum(l.net_pay for l in lines)
                variance = t_gross - t_taxes - t_benefits - t_garnishments - t_net

                rnum = PayrollReconciliation.generate_reconciliation_number(tenant)
                PayrollReconciliation.unscoped.get_or_create(
                    tenant=tenant, reconciliation_number=rnum,
                    defaults={
                        'payroll_journal': journal,
                        'reconciliation_date': journal.pay_date + timedelta(days=1),
                        'total_gross': t_gross,
                        'total_taxes': t_taxes,
                        'total_benefits': t_benefits,
                        'total_garnishments': t_garnishments,
                        'total_net': t_net,
                        'variance_amount': variance,
                        'status': 'reconciled' if variance == Decimal('0.00') else 'exception',
                        'reconciled_by': users[0],
                        'notes': 'Auto-generated reconciliation from seed data.',
                    }
                )

        self.stdout.write(
            f'  Created PR data (employees, tax withholdings, benefit plans, '
            f'enrollments, garnishments, workers comp classes & assignments, '
            f'payroll journals with lines, tax remittances, reconciliations)'
        )

    # =================================================================
    # PROJECT / JOB COSTING
    # =================================================================

    def _seed_pj_data(self):
        """Seed project/job costing sample data."""
        from apps.project_costing.models import (
            Project, WBSElement, ProjectBudget, BillingRule,
            TimeEntry, ExpenseEntry,
            RevenueRecognition, ProjectMilestone,
            ProjectInvoice, ProjectInvoiceLine,
            ProfitabilitySnapshot, ResourceAssignment,
        )
        from apps.general_ledger.models import Account
        from apps.payroll.models import Employee
        from apps.tenants.managers import set_current_tenant

        tenants = Tenant.objects.all()
        if not tenants.exists():
            self.stdout.write('  No tenants found. Skipping PJ seeding.')
            return

        for tenant in tenants:
            set_current_tenant(tenant)

            # --- GL accounts (revenue + expense) ---
            revenue_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['REV', 'REVENUE', 'INC', 'OI']
            )[:5])
            expense_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['EXP', 'EXPENSE', 'OE']
            )[:10])
            all_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )[:15])

            if len(revenue_accounts) < 1:
                revenue_accounts = all_accounts[:3]
            if len(expense_accounts) < 2:
                expense_accounts = all_accounts[3:10] if len(all_accounts) > 3 else all_accounts

            if len(revenue_accounts) < 1 or len(expense_accounts) < 1:
                self.stdout.write(f'  Skipping PJ for {tenant.name}: not enough GL accounts.')
                continue

            # --- Employees ---
            employees = list(Employee.unscoped.filter(tenant=tenant, is_active=True))
            if not employees:
                self.stdout.write(f'  Skipping PJ for {tenant.name}: no employees. Run --pr first.')
                continue

            users = list(CustomUser.objects.all()[:3])
            fiscal_periods = list(FiscalPeriod.unscoped.filter(tenant=tenant).order_by('start_date')[:6])

            # =============================================================
            # 1. Projects (5)
            # =============================================================
            projects_data = [
                {
                    'name': 'Corporate HQ Renovation',
                    'description': 'Full interior renovation of the corporate headquarters building.',
                    'client_name': 'Acme Corporation',
                    'client_contact': 'James Reed, james@acme.com',
                    'status': 'active',
                    'billing_type': 'fixed_price',
                    'contract_amount': Decimal('450000.00'),
                    'budget_amount': Decimal('400000.00'),
                    'retention_percentage': Decimal('10.00'),
                    'start_days_ago': 180,
                    'end_days_future': 120,
                },
                {
                    'name': 'ERP System Implementation',
                    'description': 'Enterprise resource planning system deployment and customization.',
                    'client_name': 'Beta Industries',
                    'client_contact': 'Maria Lopez, maria@beta.com',
                    'status': 'active',
                    'billing_type': 'time_materials',
                    'contract_amount': Decimal('320000.00'),
                    'budget_amount': Decimal('280000.00'),
                    'retention_percentage': Decimal('5.00'),
                    'start_days_ago': 90,
                    'end_days_future': 270,
                },
                {
                    'name': 'Highway Bridge Repair',
                    'description': 'Structural repair and reinforcement of Route 66 overpass.',
                    'client_name': 'State DOT',
                    'client_contact': 'Tom Harris, tom@statedot.gov',
                    'status': 'active',
                    'billing_type': 'cost_plus',
                    'contract_amount': Decimal('850000.00'),
                    'budget_amount': Decimal('780000.00'),
                    'retention_percentage': Decimal('10.00'),
                    'start_days_ago': 240,
                    'end_days_future': 60,
                },
                {
                    'name': 'Mobile App Development',
                    'description': 'Cross-platform mobile application for customer portal.',
                    'client_name': 'TechStart LLC',
                    'client_contact': 'Anna Kim, anna@techstart.io',
                    'status': 'planning',
                    'billing_type': 'fixed_price',
                    'contract_amount': Decimal('175000.00'),
                    'budget_amount': Decimal('150000.00'),
                    'retention_percentage': Decimal('0.00'),
                    'start_days_ago': 10,
                    'end_days_future': 350,
                },
                {
                    'name': 'Warehouse Automation Phase 1',
                    'description': 'Install conveyor systems and automated picking stations.',
                    'client_name': 'Global Logistics Inc.',
                    'client_contact': 'Dan Nguyen, dan@globallog.com',
                    'status': 'completed',
                    'billing_type': 'time_materials',
                    'contract_amount': Decimal('220000.00'),
                    'budget_amount': Decimal('200000.00'),
                    'retention_percentage': Decimal('5.00'),
                    'start_days_ago': 400,
                    'end_days_future': -30,
                },
            ]

            projects = []
            for pd in projects_data:
                proj, created = Project.unscoped.get_or_create(
                    tenant=tenant,
                    project_number=Project.generate_project_number(tenant),
                    defaults={
                        'name': pd['name'],
                        'description': pd['description'],
                        'client_name': pd['client_name'],
                        'client_contact': pd['client_contact'],
                        'status': pd['status'],
                        'billing_type': pd['billing_type'],
                        'contract_amount': pd['contract_amount'],
                        'budget_amount': pd['budget_amount'],
                        'retention_percentage': pd['retention_percentage'],
                        'start_date': date.today() - timedelta(days=pd['start_days_ago']),
                        'end_date': date.today() + timedelta(days=pd['end_days_future']),
                        'manager': employees[0] if employees else None,
                        'revenue_account': random.choice(revenue_accounts),
                        'expense_account': random.choice(expense_accounts),
                        'is_active': pd['status'] != 'cancelled',
                    }
                )
                projects.append(proj)

            # =============================================================
            # 2. WBS Elements (per project, 2-3 each)
            # =============================================================
            wbs_templates = [
                [
                    {'code': '1000', 'name': 'Design & Planning', 'level': 1, 'order': 1,
                     'hours': Decimal('500'), 'amount': Decimal('75000.00')},
                    {'code': '2000', 'name': 'Construction', 'level': 1, 'order': 2,
                     'hours': Decimal('2000'), 'amount': Decimal('250000.00')},
                    {'code': '3000', 'name': 'Finishing & Inspection', 'level': 1, 'order': 3,
                     'hours': Decimal('300'), 'amount': Decimal('75000.00')},
                ],
                [
                    {'code': '1000', 'name': 'Requirements & Analysis', 'level': 1, 'order': 1,
                     'hours': Decimal('400'), 'amount': Decimal('60000.00')},
                    {'code': '2000', 'name': 'Development & Configuration', 'level': 1, 'order': 2,
                     'hours': Decimal('1200'), 'amount': Decimal('160000.00')},
                    {'code': '3000', 'name': 'Testing & Go-Live', 'level': 1, 'order': 3,
                     'hours': Decimal('400'), 'amount': Decimal('60000.00')},
                ],
                [
                    {'code': '1000', 'name': 'Site Prep & Demolition', 'level': 1, 'order': 1,
                     'hours': Decimal('800'), 'amount': Decimal('200000.00')},
                    {'code': '2000', 'name': 'Structural Work', 'level': 1, 'order': 2,
                     'hours': Decimal('2500'), 'amount': Decimal('450000.00')},
                    {'code': '3000', 'name': 'Deck & Surface', 'level': 1, 'order': 3,
                     'hours': Decimal('600'), 'amount': Decimal('130000.00')},
                ],
                [
                    {'code': '1000', 'name': 'UI/UX Design', 'level': 1, 'order': 1,
                     'hours': Decimal('200'), 'amount': Decimal('30000.00')},
                    {'code': '2000', 'name': 'Backend Development', 'level': 1, 'order': 2,
                     'hours': Decimal('600'), 'amount': Decimal('80000.00')},
                    {'code': '3000', 'name': 'QA & Deployment', 'level': 1, 'order': 3,
                     'hours': Decimal('200'), 'amount': Decimal('40000.00')},
                ],
                [
                    {'code': '1000', 'name': 'Equipment Procurement', 'level': 1, 'order': 1,
                     'hours': Decimal('100'), 'amount': Decimal('80000.00')},
                    {'code': '2000', 'name': 'Installation & Wiring', 'level': 1, 'order': 2,
                     'hours': Decimal('800'), 'amount': Decimal('100000.00')},
                ],
            ]

            all_wbs = {}  # project_pk -> list of WBSElement
            for i, proj in enumerate(projects):
                wbs_list = []
                for wbs_data in wbs_templates[i % len(wbs_templates)]:
                    wbs, _ = WBSElement.unscoped.get_or_create(
                        tenant=tenant,
                        project=proj,
                        code=wbs_data['code'],
                        defaults={
                            'name': wbs_data['name'],
                            'level': wbs_data['level'],
                            'display_order': wbs_data['order'],
                            'budget_hours': wbs_data['hours'],
                            'budget_amount': wbs_data['amount'],
                            'is_billable': True,
                            'is_active': True,
                        }
                    )
                    wbs_list.append(wbs)
                all_wbs[proj.pk] = wbs_list

            # =============================================================
            # 3. Project Budgets (per WBS element)
            # =============================================================
            for proj in projects:
                for wbs in all_wbs.get(proj.pk, []):
                    ProjectBudget.unscoped.get_or_create(
                        tenant=tenant,
                        project=proj,
                        wbs_element=wbs,
                        gl_account=random.choice(expense_accounts),
                        defaults={
                            'description': f'Budget for {wbs.name}',
                            'budget_hours': wbs.budget_hours,
                            'budget_rate': Decimal('75.00'),
                            'budget_amount': wbs.budget_amount,
                            'revised_amount': wbs.budget_amount,
                            'fiscal_period': fiscal_periods[0] if fiscal_periods else None,
                        }
                    )

            # =============================================================
            # 4. Billing Rules (per project)
            # =============================================================
            billing_rule_templates = [
                {'desc': 'Standard Hourly Rate', 'rate_type': 'hourly', 'rate': Decimal('125.00'), 'markup': Decimal('0.00')},
                {'desc': 'Senior Staff Rate', 'rate_type': 'hourly', 'rate': Decimal('175.00'), 'markup': Decimal('0.00')},
                {'desc': 'Expense Markup', 'rate_type': 'percentage', 'rate': Decimal('0.00'), 'markup': Decimal('15.00')},
            ]
            for proj in projects[:3]:  # billing rules for active projects
                for br_data in billing_rule_templates[:2]:
                    BillingRule.unscoped.get_or_create(
                        tenant=tenant,
                        project=proj,
                        description=br_data['desc'],
                        defaults={
                            'rate_type': br_data['rate_type'],
                            'rate': br_data['rate'],
                            'markup_percentage': br_data['markup'],
                            'effective_date': proj.start_date,
                            'is_active': True,
                        }
                    )

            # =============================================================
            # 5. Time Entries
            # =============================================================
            time_descriptions = [
                'Design review meeting', 'Code development sprint',
                'Client requirements gathering', 'Testing and QA',
                'Documentation update', 'Architecture planning',
                'Bug fixing session', 'Database optimization',
                'Deployment and configuration', 'Stakeholder presentation',
            ]
            for proj in projects[:3]:  # time entries for active projects
                wbs_list = all_wbs.get(proj.pk, [])
                for k in range(random.randint(8, 15)):
                    emp = random.choice(employees)
                    hours = Decimal(str(random.choice([2, 4, 6, 8])))
                    rate = Decimal(str(random.choice([75, 100, 125, 150])))
                    entry_date = date.today() - timedelta(days=random.randint(1, 120))
                    is_billable = random.random() > 0.15
                    TimeEntry.unscoped.create(
                        tenant=tenant,
                        project=proj,
                        wbs_element=random.choice(wbs_list) if wbs_list else None,
                        employee=emp,
                        entry_date=entry_date,
                        hours=hours,
                        hourly_rate=rate,
                        description=random.choice(time_descriptions),
                        is_billable=is_billable,
                        billing_status='unbilled' if is_billable else 'non_billable',
                        approved_by=users[0] if users and random.random() > 0.3 else None,
                        approved_date=entry_date if users and random.random() > 0.3 else None,
                    )

            # =============================================================
            # 6. Expense Entries
            # =============================================================
            expense_items = [
                ('Equipment rental - Excavator', Decimal('2500.00'), 'Heavy Machinery Co.'),
                ('Software licenses', Decimal('1200.00'), 'Microsoft'),
                ('Travel - Client site visit', Decimal('850.00'), 'Delta Airlines'),
                ('Subcontractor - Electrical', Decimal('4500.00'), 'Spark Electric LLC'),
                ('Office supplies', Decimal('180.00'), 'Staples'),
                ('Safety equipment', Decimal('620.00'), 'Safety First Inc.'),
                ('Concrete materials', Decimal('3200.00'), 'BuildMart Supply'),
                ('Cloud hosting fees', Decimal('450.00'), 'AWS'),
            ]
            for proj in projects[:3]:
                wbs_list = all_wbs.get(proj.pk, [])
                for _ in range(random.randint(3, 6)):
                    desc, amt, vendor = random.choice(expense_items)
                    is_billable = random.random() > 0.2
                    markup = Decimal('15.00') if is_billable and random.random() > 0.5 else Decimal('0.00')
                    ExpenseEntry.unscoped.create(
                        tenant=tenant,
                        project=proj,
                        wbs_element=random.choice(wbs_list) if wbs_list else None,
                        gl_account=random.choice(expense_accounts),
                        entry_date=date.today() - timedelta(days=random.randint(5, 90)),
                        description=desc,
                        amount=amt,
                        vendor_name=vendor,
                        is_billable=is_billable,
                        markup_percentage=markup,
                        receipt_reference=f'REC-{random.randint(1000, 9999)}',
                    )

            # =============================================================
            # 7. Revenue Recognition
            # =============================================================
            if fiscal_periods:
                for proj in projects[:3]:
                    pct = random.choice([25, 40, 55, 70, 85])
                    contract = proj.contract_amount
                    cumulative = contract * Decimal(str(pct)) / Decimal('100')
                    prior = cumulative * Decimal('0.6')
                    this_period = cumulative - prior
                    RevenueRecognition.unscoped.create(
                        tenant=tenant,
                        project=proj,
                        fiscal_period=fiscal_periods[0],
                        recognition_date=date.today() - timedelta(days=30),
                        method='percentage_complete',
                        completion_percentage=Decimal(str(pct)),
                        contract_amount=contract,
                        total_recognized_prior=prior,
                        recognized_this_period=this_period,
                        cumulative_recognized=cumulative,
                        status='posted',
                        notes=f'Revenue recognition at {pct}% completion.',
                    )

            # =============================================================
            # 8. Milestones
            # =============================================================
            milestone_templates = [
                [
                    ('Design Approval', Decimal('45000.00'), 'pending', 30),
                    ('Phase 1 Complete', Decimal('135000.00'), 'completed', 90),
                    ('Final Inspection', Decimal('135000.00'), 'pending', 180),
                ],
                [
                    ('Requirements Sign-off', Decimal('32000.00'), 'completed', 30),
                    ('UAT Complete', Decimal('96000.00'), 'pending', 180),
                    ('Go-Live', Decimal('96000.00'), 'pending', 270),
                ],
                [
                    ('Demolition Complete', Decimal('85000.00'), 'completed', 60),
                    ('Structural Completion', Decimal('425000.00'), 'pending', 200),
                    ('Final Handover', Decimal('170000.00'), 'pending', 300),
                ],
            ]
            for i, proj in enumerate(projects[:3]):
                for m_name, m_amount, m_status, days_offset in milestone_templates[i]:
                    actual = date.today() - timedelta(days=random.randint(1, 30)) if m_status == 'completed' else None
                    pct = Decimal('100') if m_status == 'completed' else Decimal(str(random.randint(0, 60)))
                    ProjectMilestone.unscoped.get_or_create(
                        tenant=tenant,
                        project=proj,
                        name=m_name,
                        defaults={
                            'description': f'Milestone: {m_name}',
                            'amount': m_amount,
                            'target_date': proj.start_date + timedelta(days=days_offset),
                            'actual_date': actual,
                            'status': m_status,
                            'completion_percentage': pct,
                        }
                    )

            # =============================================================
            # 9. Project Invoices with Lines
            # =============================================================
            for proj in projects[:3]:
                for inv_i in range(random.randint(1, 3)):
                    inv_num = ProjectInvoice.generate_invoice_number(tenant)
                    inv_date = date.today() - timedelta(days=random.randint(10, 90))
                    subtotal = Decimal(str(random.randint(15000, 60000)))
                    retention = subtotal * proj.retention_percentage / Decimal('100')
                    tax = subtotal * Decimal('0.08')
                    total = subtotal - retention + tax
                    status = random.choice(['draft', 'approved', 'sent', 'paid'])

                    invoice, created = ProjectInvoice.unscoped.get_or_create(
                        tenant=tenant,
                        invoice_number=inv_num,
                        defaults={
                            'project': proj,
                            'invoice_date': inv_date,
                            'due_date': inv_date + timedelta(days=30),
                            'description': f'Progress billing #{inv_i + 1} for {proj.name}',
                            'subtotal': subtotal,
                            'retention_amount': retention,
                            'tax_amount': tax,
                            'total_amount': total,
                            'status': status,
                            'fiscal_period': fiscal_periods[0] if fiscal_periods else None,
                            'notes': f'Auto-generated invoice from seed data.',
                        }
                    )

                    if created:
                        wbs_list = all_wbs.get(proj.pk, [])
                        line_types = ['time', 'expense', 'milestone', 'other']
                        for line_i in range(random.randint(2, 4)):
                            qty = Decimal(str(random.randint(10, 80)))
                            unit_price = Decimal(str(random.choice([75, 100, 125, 150, 200])))
                            ProjectInvoiceLine.objects.create(
                                invoice=invoice,
                                description=f'{random.choice(["Engineering services", "Materials", "Consulting", "Travel expenses", "Subcontractor work"])} - Period {inv_i + 1}',
                                quantity=qty,
                                unit_price=unit_price,
                                wbs_element=random.choice(wbs_list) if wbs_list else None,
                                line_type=random.choice(line_types),
                            )

            # =============================================================
            # 10. Profitability Snapshots
            # =============================================================
            for proj in projects[:3]:
                budget = proj.budget_amount
                actual_cost = budget * Decimal(str(random.randint(40, 90))) / Decimal('100')
                actual_revenue = proj.contract_amount * Decimal(str(random.randint(30, 80))) / Decimal('100')
                committed = budget * Decimal('0.1')
                earned = budget * Decimal(str(random.randint(35, 85))) / Decimal('100')
                eac = actual_cost + (budget - earned)
                etc = eac - actual_cost
                cv = earned - actual_cost
                sv = earned - (budget * Decimal('0.5'))
                cpi = earned / actual_cost if actual_cost else Decimal('1.0000')
                spi = earned / (budget * Decimal('0.5')) if budget else Decimal('1.0000')

                ProfitabilitySnapshot.unscoped.create(
                    tenant=tenant,
                    project=proj,
                    snapshot_date=date.today() - timedelta(days=random.randint(1, 15)),
                    fiscal_period=fiscal_periods[0] if fiscal_periods else None,
                    budget_amount=budget,
                    actual_cost=actual_cost,
                    actual_revenue=actual_revenue,
                    committed_cost=committed,
                    estimate_at_completion=eac,
                    estimate_to_complete=etc,
                    earned_value=earned,
                    cost_variance=cv,
                    schedule_variance=sv,
                    cost_performance_index=min(cpi, Decimal('9.9999')),
                    schedule_performance_index=min(spi, Decimal('9.9999')),
                    notes='Auto-generated snapshot from seed data.',
                )

            # =============================================================
            # 11. Resource Assignments
            # =============================================================
            roles = ['Project Manager', 'Lead Engineer', 'Developer', 'QA Analyst',
                     'Business Analyst', 'Architect', 'Technician', 'Designer']
            for proj in projects[:4]:
                wbs_list = all_wbs.get(proj.pk, [])
                assigned_emps = random.sample(employees, min(len(employees), random.randint(2, 4)))
                for emp in assigned_emps:
                    alloc = Decimal(str(random.choice([25, 50, 75, 100])))
                    planned = Decimal(str(random.randint(80, 400)))
                    actual = planned * Decimal(str(random.randint(20, 95))) / Decimal('100')
                    ResourceAssignment.unscoped.get_or_create(
                        tenant=tenant,
                        project=proj,
                        employee=emp,
                        defaults={
                            'wbs_element': random.choice(wbs_list) if wbs_list else None,
                            'role': random.choice(roles),
                            'allocation_percentage': alloc,
                            'start_date': proj.start_date,
                            'end_date': proj.end_date,
                            'planned_hours': planned,
                            'actual_hours': actual,
                            'is_active': proj.status in ('active', 'planning'),
                        }
                    )

        self.stdout.write(
            f'  Created PJ data (projects, WBS elements, budgets, billing rules, '
            f'time entries, expenses, revenue recognition, milestones, '
            f'invoices with lines, profitability snapshots, resource assignments)'
        )

    def _seed_me_data(self):
        from apps.multi_entity.models import (
            Entity, IntercompanyTransaction, IntercompanyBalance,
            CurrencyTranslationRule, TranslationAdjustment,
            ConsolidationGroup, ConsolidationRun, EliminationRule,
            EliminationEntry, MinorityInterest,
            TransferPricingPolicy, TransferPricingTransaction,
            LocalGAAPAdjustment, RegulatoryReport,
        )
        from apps.general_ledger.models import Account
        from apps.tenants.managers import set_current_tenant

        tenants = Tenant.objects.all()
        if not tenants.exists():
            self.stdout.write('  No tenants found. Skipping ME seeding.')
            return

        for tenant in tenants:
            set_current_tenant(tenant)

            # ---- Prerequisites ----
            usd = Currency.objects.filter(code='USD').first()
            eur = Currency.objects.filter(code='EUR').first()
            gbp = Currency.objects.filter(code='GBP').first()
            jpy = Currency.objects.filter(code='JPY').first()

            if not usd:
                self.stdout.write(f'  Skipping ME for {tenant.name}: no USD currency.')
                continue

            # Fallback currencies
            if not eur:
                eur = usd
            if not gbp:
                gbp = usd
            if not jpy:
                jpy = usd

            users = list(CustomUser.objects.all()[:3])
            if not users:
                continue
            user = users[0]

            fiscal_periods = list(FiscalPeriod.unscoped.filter(
                tenant=tenant
            ).order_by('start_date')[:6])
            if not fiscal_periods:
                self.stdout.write(f'  Skipping ME for {tenant.name}: no fiscal periods.')
                continue

            account_types = list(AccountType.objects.all())

            # Get GL accounts by type for mapping
            asset_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['AST', 'ASSET', 'CA', 'NCA']
            )[:10])
            liability_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['CL', 'LIA', 'LIABILITY', 'NCL']
            )[:10])
            equity_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['EQ', 'EQUITY', 'OE']
            )[:5])
            revenue_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['REV', 'REVENUE', 'OI']
            )[:5])
            expense_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['EXP', 'EXPENSE', 'OE']
            )[:10])

            # Fallback: get any non-header accounts
            all_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False
            )[:20])
            if len(asset_accounts) < 2:
                asset_accounts = all_accounts[:4]
            if len(liability_accounts) < 2:
                liability_accounts = all_accounts[4:8] if len(all_accounts) > 4 else all_accounts[:4]
            if len(equity_accounts) < 2:
                equity_accounts = all_accounts[8:12] if len(all_accounts) > 8 else all_accounts[:4]
            if len(revenue_accounts) < 2:
                revenue_accounts = all_accounts[12:16] if len(all_accounts) > 12 else all_accounts[:4]
            if len(expense_accounts) < 2:
                expense_accounts = all_accounts[16:20] if len(all_accounts) > 16 else all_accounts[:4]

            if len(all_accounts) < 4:
                self.stdout.write(f'  Skipping ME for {tenant.name}: not enough GL accounts.')
                continue

            # =============================================================
            # 1. Entities (1 parent + 4 subsidiaries/branches)
            # =============================================================
            entities_data = [
                {
                    'code': 'HQ',
                    'name': 'Corporate Headquarters',
                    'legal_name': f'{tenant.name} Holdings Inc.',
                    'entity_type': 'parent',
                    'parent': None,
                    'functional_currency': usd,
                    'ownership_percentage': Decimal('100.0000'),
                    'consolidation_method': 'full',
                    'tax_id': '12-3456789',
                    'country': 'United States',
                    'local_gaap': 'US GAAP',
                    'status': 'active',
                },
                {
                    'code': 'EU-SUB',
                    'name': 'European Operations',
                    'legal_name': f'{tenant.name} Europe GmbH',
                    'entity_type': 'subsidiary',
                    'parent': 'HQ',
                    'functional_currency': eur,
                    'ownership_percentage': Decimal('85.0000'),
                    'consolidation_method': 'full',
                    'tax_id': 'DE123456789',
                    'country': 'Germany',
                    'local_gaap': 'IFRS',
                    'status': 'active',
                },
                {
                    'code': 'UK-BR',
                    'name': 'UK Branch Office',
                    'legal_name': f'{tenant.name} UK Ltd.',
                    'entity_type': 'branch',
                    'parent': 'EU-SUB',
                    'functional_currency': gbp,
                    'ownership_percentage': Decimal('100.0000'),
                    'consolidation_method': 'full',
                    'tax_id': 'GB987654321',
                    'country': 'United Kingdom',
                    'local_gaap': 'UK GAAP',
                    'status': 'active',
                },
                {
                    'code': 'ASIA-JV',
                    'name': 'Asia Pacific Joint Venture',
                    'legal_name': f'{tenant.name} Asia Pacific KK',
                    'entity_type': 'joint_venture',
                    'parent': 'HQ',
                    'functional_currency': jpy,
                    'ownership_percentage': Decimal('51.0000'),
                    'consolidation_method': 'proportional',
                    'tax_id': 'JP-1234567890',
                    'country': 'Japan',
                    'local_gaap': 'J-GAAP',
                    'status': 'active',
                },
                {
                    'code': 'US-DIV',
                    'name': 'Manufacturing Division',
                    'legal_name': f'{tenant.name} Manufacturing LLC',
                    'entity_type': 'division',
                    'parent': 'HQ',
                    'functional_currency': usd,
                    'ownership_percentage': Decimal('100.0000'),
                    'consolidation_method': 'full',
                    'tax_id': '98-7654321',
                    'country': 'United States',
                    'local_gaap': 'US GAAP',
                    'status': 'active',
                },
            ]

            entities = {}
            for ed in entities_data:
                parent_ref = ed.pop('parent')
                parent_entity = entities.get(parent_ref) if parent_ref else None
                entity, _ = Entity.unscoped.get_or_create(
                    tenant=tenant,
                    code=ed['code'],
                    defaults={
                        **ed,
                        'parent': parent_entity,
                        'ic_receivable_account': asset_accounts[0] if asset_accounts else None,
                        'ic_payable_account': liability_accounts[0] if liability_accounts else None,
                        'cta_account': equity_accounts[0] if equity_accounts else None,
                        'minority_interest_account': equity_accounts[1] if len(equity_accounts) > 1 else (equity_accounts[0] if equity_accounts else None),
                    }
                )
                entities[ed['code']] = entity

            entity_list = list(entities.values())
            hq = entities.get('HQ')
            eu_sub = entities.get('EU-SUB')
            uk_br = entities.get('UK-BR')
            asia_jv = entities.get('ASIA-JV')
            us_div = entities.get('US-DIV')

            # =============================================================
            # 2. Intercompany Transactions
            # =============================================================
            ic_txns_data = [
                {
                    'from': hq, 'to': eu_sub,
                    'type': 'sale', 'amount': Decimal('150000.00'),
                    'desc': 'IC sale of finished goods from HQ to EU subsidiary',
                    'status': 'posted',
                },
                {
                    'from': eu_sub, 'to': uk_br,
                    'type': 'service', 'amount': Decimal('45000.00'),
                    'desc': 'Management consulting services from EU to UK branch',
                    'status': 'confirmed',
                },
                {
                    'from': hq, 'to': asia_jv,
                    'type': 'loan', 'amount': Decimal('500000.00'),
                    'desc': 'Intercompany loan from HQ to Asia JV for expansion',
                    'status': 'posted',
                },
                {
                    'from': us_div, 'to': hq,
                    'type': 'expense_allocation', 'amount': Decimal('75000.00'),
                    'desc': 'Shared services cost allocation from manufacturing to HQ',
                    'status': 'confirmed',
                },
                {
                    'from': asia_jv, 'to': eu_sub,
                    'type': 'purchase', 'amount': Decimal('200000.00'),
                    'desc': 'IC purchase of raw materials from EU subsidiary',
                    'status': 'draft',
                },
                {
                    'from': hq, 'to': us_div,
                    'type': 'capital', 'amount': Decimal('1000000.00'),
                    'desc': 'Capital contribution to manufacturing division',
                    'status': 'posted',
                },
                {
                    'from': eu_sub, 'to': hq,
                    'type': 'dividend', 'amount': Decimal('250000.00'),
                    'desc': 'Dividend distribution from EU subsidiary to parent',
                    'status': 'pending',
                },
                {
                    'from': uk_br, 'to': hq,
                    'type': 'service', 'amount': Decimal('30000.00'),
                    'desc': 'IT support services from UK branch to HQ',
                    'status': 'cancelled',
                },
            ]

            ic_transactions = []
            for idx, txn_data in enumerate(ic_txns_data):
                txn_num = f"ICX-2026-{idx + 1:04d}"
                txn, created = IntercompanyTransaction.unscoped.get_or_create(
                    tenant=tenant,
                    transaction_number=txn_num,
                    defaults={
                        'from_entity': txn_data['from'],
                        'to_entity': txn_data['to'],
                        'transaction_type': txn_data['type'],
                        'date': fiscal_periods[min(idx, len(fiscal_periods) - 1)].start_date + timedelta(days=random.randint(1, 25)),
                        'description': txn_data['desc'],
                        'amount': txn_data['amount'],
                        'currency': usd,
                        'exchange_rate': Decimal('1.00000000'),
                        'fiscal_period': fiscal_periods[min(idx, len(fiscal_periods) - 1)],
                        'status': txn_data['status'],
                        'created_by': user,
                        'confirmed_by': users[1] if len(users) > 1 and txn_data['status'] in ('confirmed', 'posted') else None,
                        'confirmed_at': timezone.now() if txn_data['status'] in ('confirmed', 'posted') else None,
                    }
                )
                ic_transactions.append(txn)

            # =============================================================
            # 3. Intercompany Balances
            # =============================================================
            balance_pairs = [
                (hq, eu_sub, Decimal('150000.00'), True),
                (hq, asia_jv, Decimal('500000.00'), False),
                (hq, us_div, Decimal('1000000.00'), True),
                (eu_sub, uk_br, Decimal('45000.00'), False),
                (eu_sub, hq, Decimal('-250000.00'), False),
            ]
            for from_e, to_e, bal, reconciled in balance_pairs:
                IntercompanyBalance.unscoped.get_or_create(
                    tenant=tenant,
                    from_entity=from_e,
                    to_entity=to_e,
                    fiscal_period=fiscal_periods[0],
                    currency=usd,
                    defaults={
                        'balance': bal,
                        'is_reconciled': reconciled,
                        'last_reconciled_at': timezone.now() if reconciled else None,
                    }
                )

            # =============================================================
            # 4. Currency Translation Rules
            # =============================================================
            acct_types = list(AccountType.objects.all())
            rules_data = [
                ('Assets - Current Rate', 'account_type', 'current', None),
                ('Liabilities - Current Rate', 'account_type', 'current', None),
                ('Equity - Historical Rate', 'account_type', 'historical', None),
                ('Revenue - Average Rate', 'account_type', 'average', None),
                ('Expenses - Average Rate', 'account_type', 'average', None),
            ]
            for idx, (name, scope, rate_type, fixed) in enumerate(rules_data):
                CurrencyTranslationRule.unscoped.get_or_create(
                    tenant=tenant,
                    name=name,
                    defaults={
                        'account_scope': scope,
                        'account_type': acct_types[idx] if idx < len(acct_types) else None,
                        'rate_type': rate_type,
                        'fixed_rate': fixed,
                        'is_active': True,
                    }
                )

            # =============================================================
            # 5. Translation Adjustments
            # =============================================================
            foreign_entities = [eu_sub, uk_br, asia_jv]
            for ent in foreign_entities:
                if ent.functional_currency == usd:
                    continue
                cta_amt = Decimal(str(random.randint(-50000, 50000)))
                TranslationAdjustment.unscoped.get_or_create(
                    tenant=tenant,
                    entity=ent,
                    fiscal_period=fiscal_periods[0],
                    defaults={
                        'from_currency': ent.functional_currency,
                        'to_currency': usd,
                        'total_assets_translated': Decimal(str(random.randint(500000, 2000000))),
                        'total_liabilities_translated': Decimal(str(random.randint(200000, 800000))),
                        'total_equity_translated': Decimal(str(random.randint(200000, 1000000))),
                        'total_income_translated': Decimal(str(random.randint(100000, 500000))),
                        'total_expense_translated': Decimal(str(random.randint(80000, 400000))),
                        'cta_amount': cta_amt,
                        'cta_cumulative': cta_amt,
                        'calculated_by': user,
                    }
                )

            # =============================================================
            # 6. Consolidation Groups
            # =============================================================
            group, _ = ConsolidationGroup.unscoped.get_or_create(
                tenant=tenant,
                code='GRP-GLOBAL',
                defaults={
                    'name': 'Global Consolidation Group',
                    'parent_entity': hq,
                    'reporting_currency': usd,
                    'is_active': True,
                    'description': 'Full group consolidation including all entities.',
                }
            )
            group.entities.set(entity_list)

            group_eu, _ = ConsolidationGroup.unscoped.get_or_create(
                tenant=tenant,
                code='GRP-EU',
                defaults={
                    'name': 'European Sub-Group',
                    'parent_entity': eu_sub,
                    'reporting_currency': eur,
                    'is_active': True,
                    'description': 'European regional consolidation sub-group.',
                }
            )
            group_eu.entities.set([eu_sub, uk_br])

            # =============================================================
            # 7. Elimination Rules
            # =============================================================
            elim_rules_data = [
                {
                    'name': 'Eliminate IC Receivables/Payables',
                    'rule_type': 'ic_receivable_payable',
                    'debit': liability_accounts[0],
                    'credit': asset_accounts[0],
                    'priority': 10,
                },
                {
                    'name': 'Eliminate IC Revenue/COGS',
                    'rule_type': 'ic_revenue_expense',
                    'debit': revenue_accounts[0] if revenue_accounts else all_accounts[0],
                    'credit': expense_accounts[0] if expense_accounts else all_accounts[1],
                    'priority': 20,
                },
                {
                    'name': 'Eliminate IC Dividends',
                    'rule_type': 'ic_dividend',
                    'debit': revenue_accounts[1] if len(revenue_accounts) > 1 else (revenue_accounts[0] if revenue_accounts else all_accounts[0]),
                    'credit': equity_accounts[0] if equity_accounts else all_accounts[2],
                    'priority': 30,
                },
                {
                    'name': 'Eliminate Investment in Subsidiaries',
                    'rule_type': 'ic_investment_equity',
                    'debit': equity_accounts[0] if equity_accounts else all_accounts[2],
                    'credit': asset_accounts[1] if len(asset_accounts) > 1 else asset_accounts[0],
                    'priority': 40,
                },
            ]

            elim_rules = []
            for rd in elim_rules_data:
                rule, _ = EliminationRule.unscoped.get_or_create(
                    tenant=tenant,
                    name=rd['name'],
                    defaults={
                        'rule_type': rd['rule_type'],
                        'consolidation_group': group,
                        'debit_account': rd['debit'],
                        'credit_account': rd['credit'],
                        'is_auto': True,
                        'is_active': True,
                        'priority': rd['priority'],
                    }
                )
                elim_rules.append(rule)

            # =============================================================
            # 8. Consolidation Runs
            # =============================================================
            runs_data = [
                ('CON-2026-0001', fiscal_periods[0], 'completed', Decimal('195000.00'), Decimal('24500.00')),
                ('CON-2026-0002', fiscal_periods[1] if len(fiscal_periods) > 1 else fiscal_periods[0], 'draft', Decimal('0.00'), Decimal('0.00')),
                ('CON-2026-0003', fiscal_periods[0], 'reversed', Decimal('100000.00'), Decimal('12000.00')),
            ]

            con_runs = []
            for run_num, fp, status, total_elim, total_nci in runs_data:
                run, _ = ConsolidationRun.unscoped.get_or_create(
                    tenant=tenant,
                    run_number=run_num,
                    defaults={
                        'consolidation_group': group,
                        'fiscal_period': fp,
                        'status': status,
                        'total_eliminations': total_elim,
                        'total_minority_interest': total_nci,
                        'total_cta': Decimal(str(random.randint(-30000, 30000))),
                        'started_at': timezone.now() - timedelta(hours=random.randint(1, 48)) if status != 'draft' else None,
                        'completed_at': timezone.now() if status in ('completed', 'reversed') else None,
                        'created_by': user,
                    }
                )
                con_runs.append(run)

            # =============================================================
            # 9. Elimination Entries (for completed run)
            # =============================================================
            completed_run = con_runs[0] if con_runs else None
            if completed_run and completed_run.status == 'completed':
                elim_entries_data = [
                    (hq, eu_sub, elim_rules[0], Decimal('150000.00'), 'Eliminate IC receivable HQ/EU-SUB'),
                    (eu_sub, uk_br, elim_rules[1], Decimal('45000.00'), 'Eliminate IC revenue EU-SUB/UK-BR'),
                ]
                for from_e, to_e, rule, amount, desc in elim_entries_data:
                    EliminationEntry.unscoped.get_or_create(
                        tenant=tenant,
                        consolidation_run=completed_run,
                        elimination_rule=rule,
                        from_entity=from_e,
                        to_entity=to_e,
                        defaults={
                            'debit_account': rule.debit_account,
                            'credit_account': rule.credit_account,
                            'amount': amount,
                            'description': desc,
                        }
                    )

            # =============================================================
            # 10. Minority Interest
            # =============================================================
            nci_entities = [(eu_sub, Decimal('15.0000')), (asia_jv, Decimal('49.0000'))]
            if completed_run:
                for ent, nci_pct in nci_entities:
                    net_income = Decimal(str(random.randint(100000, 500000)))
                    total_equity = Decimal(str(random.randint(500000, 2000000)))
                    MinorityInterest.unscoped.get_or_create(
                        tenant=tenant,
                        consolidation_run=completed_run,
                        entity=ent,
                        defaults={
                            'fiscal_period': fiscal_periods[0],
                            'minority_percentage': nci_pct,
                            'net_income': net_income,
                            'minority_share': (net_income * nci_pct / 100).quantize(Decimal('0.01')),
                            'total_equity': total_equity,
                            'minority_equity': (total_equity * nci_pct / 100).quantize(Decimal('0.01')),
                        }
                    )

            # =============================================================
            # 11. Transfer Pricing Policies
            # =============================================================
            tp_policies_data = [
                {
                    'name': 'HQ to EU Goods Transfer Policy',
                    'from': hq, 'to': eu_sub,
                    'method': 'cost_plus', 'markup': Decimal('15.0000'),
                    'status': 'active',
                    'doc': 'Cost plus 15% markup for finished goods transferred from HQ to European subsidiary. Based on comparable uncontrolled transactions in the industry.',
                },
                {
                    'name': 'EU to UK Management Services',
                    'from': eu_sub, 'to': uk_br,
                    'method': 'tnmm', 'markup': Decimal('8.5000'),
                    'status': 'active',
                    'doc': 'Transactional net margin method applied to management consulting services. Benchmark study covers FY 2024-2026.',
                },
                {
                    'name': 'HQ to Asia JV Technology License',
                    'from': hq, 'to': asia_jv,
                    'method': 'cup', 'markup': Decimal('0.0000'),
                    'status': 'active',
                    'doc': 'Comparable uncontrolled price based on market license agreements for similar technology. Royalty rate 5% of net sales.',
                },
                {
                    'name': 'Legacy Manufacturing Policy',
                    'from': us_div, 'to': hq,
                    'method': 'resale_price', 'markup': Decimal('20.0000'),
                    'status': 'expired',
                    'doc': 'Expired resale price method for internal manufacturing transfers. Replaced by new cost plus policy.',
                },
            ]

            tp_policies = []
            for idx, pd in enumerate(tp_policies_data):
                pol_num = f"TPP-2026-{idx + 1:04d}"
                policy, _ = TransferPricingPolicy.unscoped.get_or_create(
                    tenant=tenant,
                    policy_number=pol_num,
                    defaults={
                        'name': pd['name'],
                        'from_entity': pd['from'],
                        'to_entity': pd['to'],
                        'pricing_method': pd['method'],
                        'markup_percentage': pd['markup'],
                        'effective_from': date(2025, 1, 1),
                        'effective_to': date(2024, 12, 31) if pd['status'] == 'expired' else None,
                        'status': pd['status'],
                        'documentation': pd['doc'],
                        'comparable_data': 'Benchmark database: BvD Orbis, RoyaltyStat. Range: Q1-Q3 interquartile.',
                        'created_by': user,
                    }
                )
                tp_policies.append(policy)

            # =============================================================
            # 12. Transfer Pricing Transactions
            # =============================================================
            tp_txn_statuses = ['approved', 'reviewed', 'draft', 'flagged', 'approved']
            for idx, ic_txn in enumerate(ic_transactions[:5]):
                if idx >= len(tp_policies):
                    pol = tp_policies[0]
                else:
                    pol = tp_policies[idx] if tp_policies[idx].status == 'active' else tp_policies[0]

                transfer_price = ic_txn.amount
                variance_pct = Decimal(str(random.uniform(-8.0, 12.0))).quantize(Decimal('0.0001'))
                arms_length = (transfer_price / (1 + variance_pct / 100)).quantize(Decimal('0.01'))

                TransferPricingTransaction.unscoped.get_or_create(
                    tenant=tenant,
                    policy=pol,
                    intercompany_transaction=ic_txn,
                    defaults={
                        'transfer_price': transfer_price,
                        'arms_length_price': arms_length,
                        'status': tp_txn_statuses[idx % len(tp_txn_statuses)],
                        'review_notes': 'Variance within acceptable range.' if tp_txn_statuses[idx % len(tp_txn_statuses)] in ('approved', 'reviewed') else '',
                        'reviewed_by': users[1] if len(users) > 1 and tp_txn_statuses[idx % len(tp_txn_statuses)] != 'draft' else None,
                        'reviewed_at': timezone.now() if tp_txn_statuses[idx % len(tp_txn_statuses)] != 'draft' else None,
                    }
                )

            # =============================================================
            # 13. Local GAAP Adjustments
            # =============================================================
            gaap_adj_data = [
                {
                    'entity': eu_sub,
                    'type': 'measurement',
                    'from_std': 'IFRS',
                    'to_std': 'HGB (German GAAP)',
                    'amount': Decimal('35000.00'),
                    'desc': 'Revalue inventory from IFRS fair value to HGB lower of cost or market.',
                    'status': 'posted',
                },
                {
                    'entity': uk_br,
                    'type': 'reclassification',
                    'from_std': 'IFRS',
                    'to_std': 'UK GAAP (FRS 102)',
                    'amount': Decimal('12500.00'),
                    'desc': 'Reclassify finance lease to operating lease under UK GAAP.',
                    'status': 'reviewed',
                },
                {
                    'entity': asia_jv,
                    'type': 'recognition',
                    'from_std': 'IFRS',
                    'to_std': 'J-GAAP',
                    'amount': Decimal('85000.00'),
                    'desc': 'Deferred tax asset recognition difference between IFRS and J-GAAP.',
                    'status': 'draft',
                },
                {
                    'entity': hq,
                    'type': 'disclosure',
                    'from_std': 'IFRS',
                    'to_std': 'US GAAP (ASC)',
                    'amount': Decimal('0.00'),
                    'desc': 'Additional segment reporting disclosure required under US GAAP ASC 280.',
                    'status': 'draft',
                },
                {
                    'entity': eu_sub,
                    'type': 'other',
                    'from_std': 'IFRS 16',
                    'to_std': 'HGB',
                    'amount': Decimal('22000.00'),
                    'desc': 'Right-of-use asset adjustment from IFRS 16 to HGB lease treatment.',
                    'status': 'posted',
                },
            ]

            for idx, adj in enumerate(gaap_adj_data):
                adj_num = f"GAP-2026-{idx + 1:04d}"
                LocalGAAPAdjustment.unscoped.get_or_create(
                    tenant=tenant,
                    adjustment_number=adj_num,
                    defaults={
                        'entity': adj['entity'],
                        'fiscal_period': fiscal_periods[0],
                        'adjustment_type': adj['type'],
                        'from_standard': adj['from_std'],
                        'to_standard': adj['to_std'],
                        'debit_account': expense_accounts[idx % len(expense_accounts)] if expense_accounts else all_accounts[0],
                        'credit_account': liability_accounts[idx % len(liability_accounts)] if liability_accounts else all_accounts[1],
                        'amount': adj['amount'],
                        'description': adj['desc'],
                        'status': adj['status'],
                        'created_by': user,
                    }
                )

            # =============================================================
            # 14. Regulatory Reports
            # =============================================================
            reports_data = [
                {
                    'entity': eu_sub,
                    'type': 'local_fs',
                    'name': 'German Statutory Financial Statements FY2025',
                    'gaap': 'HGB',
                    'status': 'filed',
                    'ref': 'EBANZ-2025-EU-001',
                },
                {
                    'entity': uk_br,
                    'type': 'statutory',
                    'name': 'Companies House Annual Return FY2025',
                    'gaap': 'FRS 102',
                    'status': 'generated',
                    'ref': '',
                },
                {
                    'entity': asia_jv,
                    'type': 'tax_return',
                    'name': 'Japan Corporate Tax Return FY2025',
                    'gaap': 'J-GAAP',
                    'status': 'reviewed',
                    'ref': '',
                },
                {
                    'entity': hq,
                    'type': 'regulatory',
                    'name': 'SEC 10-K Annual Filing FY2025',
                    'gaap': 'US GAAP',
                    'status': 'filed',
                    'ref': 'SEC-10K-2025-001',
                },
                {
                    'entity': hq,
                    'type': 'local_fs',
                    'name': 'Consolidated Financial Statements FY2025',
                    'gaap': 'US GAAP',
                    'status': 'generated',
                    'ref': '',
                },
                {
                    'entity': eu_sub,
                    'type': 'custom',
                    'name': 'CBCR Country-by-Country Report FY2025',
                    'gaap': 'OECD BEPS',
                    'status': 'draft',
                    'ref': '',
                },
            ]

            for idx, rd in enumerate(reports_data):
                rep_num = f"REG-2026-{idx + 1:04d}"
                RegulatoryReport.unscoped.get_or_create(
                    tenant=tenant,
                    report_number=rep_num,
                    defaults={
                        'entity': rd['entity'],
                        'fiscal_period': fiscal_periods[0],
                        'report_type': rd['type'],
                        'name': rd['name'],
                        'gaap_standard': rd['gaap'],
                        'status': rd['status'],
                        'generated_at': timezone.now() if rd['status'] != 'draft' else None,
                        'generated_by': user if rd['status'] != 'draft' else None,
                        'filed_at': timezone.now() if rd['status'] == 'filed' else None,
                        'filing_reference': rd['ref'],
                        'report_data': {
                            'period': 'FY2025',
                            'entity_code': rd['entity'].code,
                            'standard': rd['gaap'],
                        },
                    }
                )

        self.stdout.write(
            f'  Created ME data (entities, IC transactions, IC balances, '
            f'translation rules, CTA adjustments, consolidation groups, '
            f'elimination rules, consolidation runs, elimination entries, '
            f'minority interest, TP policies, TP transactions, '
            f'GAAP adjustments, regulatory reports)'
        )

    def _seed_tx_data(self):
        """Seed tax management data for all tenants."""
        from datetime import date, timedelta
        from decimal import Decimal

        from apps.tax.models import (
            TaxJurisdiction, TaxRate, TaxRule, TaxGroup, TaxGroupMember,
            TaxReturn, TaxReturnLine,
            TaxDeadline,
            NexusJurisdiction, NexusActivity,
        )
        from apps.tenants.managers import set_current_tenant
        from apps.tenants.models import Tenant
        from apps.general_ledger.models import Account

        tenants = Tenant.objects.all()
        for tenant in tenants:
            set_current_tenant(tenant)

            # Get GL accounts for tax
            liability_accounts = list(Account.unscoped.filter(
                tenant=tenant, is_active=True, is_header=False,
                account_type__code__in=['LI', 'LIABILITY', 'OL']
            )[:5])
            if not liability_accounts:
                continue
            tax_payable_acct = liability_accounts[0]

            # =================================================================
            # 1. Tax Jurisdictions
            # =================================================================
            jurisdictions_data = [
                {'code': 'US-FED', 'name': 'United States Federal', 'level': 'federal', 'country': 'US', 'state_code': ''},
                {'code': 'US-CA', 'name': 'California', 'level': 'state', 'country': 'US', 'state_code': 'CA'},
                {'code': 'US-NY', 'name': 'New York', 'level': 'state', 'country': 'US', 'state_code': 'NY'},
                {'code': 'US-TX', 'name': 'Texas', 'level': 'state', 'country': 'US', 'state_code': 'TX'},
                {'code': 'US-CA-LA', 'name': 'Los Angeles County', 'level': 'county', 'country': 'US', 'state_code': 'CA'},
                {'code': 'US-NY-NYC', 'name': 'New York City', 'level': 'city', 'country': 'US', 'state_code': 'NY'},
                {'code': 'US-CA-SF', 'name': 'San Francisco', 'level': 'city', 'country': 'US', 'state_code': 'CA'},
            ]

            created_jurisdictions = {}
            fed_jurisdiction = None
            ca_jurisdiction = None

            for jd in jurisdictions_data:
                j, _ = TaxJurisdiction.unscoped.get_or_create(
                    tenant=tenant, code=jd['code'],
                    defaults={
                        'name': jd['name'],
                        'jurisdiction_level': jd['level'],
                        'country': jd['country'],
                        'state_code': jd['state_code'],
                        'is_active': True,
                    }
                )
                created_jurisdictions[jd['code']] = j
                if jd['code'] == 'US-FED':
                    fed_jurisdiction = j
                if jd['code'] == 'US-CA':
                    ca_jurisdiction = j

            # Set parent relationships
            for code in ['US-CA', 'US-NY', 'US-TX']:
                j = created_jurisdictions[code]
                if not j.parent and fed_jurisdiction:
                    j.parent = fed_jurisdiction
                    j.save()
            if ca_jurisdiction:
                for code in ['US-CA-LA', 'US-CA-SF']:
                    j = created_jurisdictions[code]
                    if not j.parent:
                        j.parent = ca_jurisdiction
                        j.save()
            ny_j = created_jurisdictions.get('US-NY')
            nyc_j = created_jurisdictions.get('US-NY-NYC')
            if ny_j and nyc_j and not nyc_j.parent:
                nyc_j.parent = ny_j
                nyc_j.save()

            # =================================================================
            # 2. Tax Rates
            # =================================================================
            rates_data = [
                {'jurisdiction': 'US-CA', 'name': 'CA State Sales Tax', 'rate': Decimal('7.25000'), 'date': date(2025, 1, 1)},
                {'jurisdiction': 'US-CA-LA', 'name': 'LA County Sales Tax', 'rate': Decimal('2.25000'), 'date': date(2025, 1, 1)},
                {'jurisdiction': 'US-CA-SF', 'name': 'SF District Tax', 'rate': Decimal('1.25000'), 'date': date(2025, 1, 1)},
                {'jurisdiction': 'US-NY', 'name': 'NY State Sales Tax', 'rate': Decimal('4.00000'), 'date': date(2025, 1, 1)},
                {'jurisdiction': 'US-NY-NYC', 'name': 'NYC Local Sales Tax', 'rate': Decimal('4.50000'), 'date': date(2025, 1, 1)},
                {'jurisdiction': 'US-TX', 'name': 'TX State Sales Tax', 'rate': Decimal('6.25000'), 'date': date(2025, 1, 1)},
            ]

            created_rates = {}
            for rd in rates_data:
                j = created_jurisdictions.get(rd['jurisdiction'])
                if not j:
                    continue
                r, _ = TaxRate.unscoped.get_or_create(
                    tenant=tenant, jurisdiction=j, rate_name=rd['name'],
                    defaults={
                        'rate': rd['rate'],
                        'effective_date': rd['date'],
                        'gl_tax_collected_account': tax_payable_acct,
                        'is_active': True,
                    }
                )
                created_rates[rd['jurisdiction']] = r

            # =================================================================
            # 3. Tax Rules
            # =================================================================
            rules_data = [
                {'code': 'CA-FOOD', 'name': 'CA Food Exemption', 'jurisdiction': 'US-CA', 'rule_type': 'exempt', 'category': 'Food - Unprepared'},
                {'code': 'CA-RX', 'name': 'CA Prescription Drug Exemption', 'jurisdiction': 'US-CA', 'rule_type': 'exempt', 'category': 'Prescription Drugs'},
                {'code': 'NY-CLOTH', 'name': 'NY Clothing Exemption (<$110)', 'jurisdiction': 'US-NY', 'rule_type': 'exempt', 'category': 'Clothing Under $110'},
                {'code': 'TX-FOOD', 'name': 'TX Grocery Exemption', 'jurisdiction': 'US-TX', 'rule_type': 'exempt', 'category': 'Groceries'},
            ]

            for rul in rules_data:
                j = created_jurisdictions.get(rul['jurisdiction'])
                if not j:
                    continue
                TaxRule.unscoped.get_or_create(
                    tenant=tenant, code=rul['code'],
                    defaults={
                        'name': rul['name'],
                        'jurisdiction': j,
                        'rule_type': rul['rule_type'],
                        'product_category': rul['category'],
                        'effective_date': date(2025, 1, 1),
                        'is_active': True,
                    }
                )

            # =================================================================
            # 4. Tax Groups
            # =================================================================
            ca_rate = created_rates.get('US-CA')
            la_rate = created_rates.get('US-CA-LA')
            sf_rate = created_rates.get('US-CA-SF')
            ny_rate = created_rates.get('US-NY')
            nyc_rate = created_rates.get('US-NY-NYC')

            if ca_rate and la_rate:
                grp, created = TaxGroup.unscoped.get_or_create(
                    tenant=tenant, code='CA-LA-COMBINED',
                    defaults={'name': 'California + LA County Combined', 'is_active': True}
                )
                if created:
                    TaxGroupMember.objects.create(tax_group=grp, tax_rate=ca_rate, priority=1)
                    TaxGroupMember.objects.create(tax_group=grp, tax_rate=la_rate, priority=2)

            if ny_rate and nyc_rate:
                grp, created = TaxGroup.unscoped.get_or_create(
                    tenant=tenant, code='NY-NYC-COMBINED',
                    defaults={'name': 'New York + NYC Combined', 'is_active': True}
                )
                if created:
                    TaxGroupMember.objects.create(tax_group=grp, tax_rate=ny_rate, priority=1)
                    TaxGroupMember.objects.create(tax_group=grp, tax_rate=nyc_rate, priority=2)

            # =================================================================
            # 5. Tax Returns
            # =================================================================
            today = date.today()
            user = tenant.owner

            returns_data = [
                {
                    'type': 'sales_tax', 'jurisdiction': 'US-CA',
                    'period_start': date(2025, 10, 1), 'period_end': date(2025, 12, 31),
                    'due_date': date(2026, 1, 31), 'status': 'filed',
                    'taxable': Decimal('250000.00'), 'tax_due': Decimal('18125.00'),
                    'net_due': Decimal('18125.00'), 'paid': Decimal('18125.00'),
                },
                {
                    'type': 'sales_tax', 'jurisdiction': 'US-NY',
                    'period_start': date(2026, 1, 1), 'period_end': date(2026, 3, 31),
                    'due_date': date(2026, 4, 20), 'status': 'draft',
                    'taxable': Decimal('180000.00'), 'tax_due': Decimal('15300.00'),
                    'net_due': Decimal('15300.00'), 'paid': Decimal('0.00'),
                },
                {
                    'type': 'income_tax', 'jurisdiction': 'US-FED',
                    'period_start': date(2025, 1, 1), 'period_end': date(2025, 12, 31),
                    'due_date': date(2026, 4, 15), 'status': 'calculated',
                    'taxable': Decimal('500000.00'), 'tax_due': Decimal('105000.00'),
                    'net_due': Decimal('105000.00'), 'paid': Decimal('80000.00'),
                },
            ]

            for rd in returns_data:
                j = created_jurisdictions.get(rd['jurisdiction'])
                if not j or not user:
                    continue
                tr, created = TaxReturn.unscoped.get_or_create(
                    tenant=tenant,
                    return_number=TaxReturn.generate_return_number(tenant),
                    defaults={
                        'return_type': rd['type'],
                        'jurisdiction': j,
                        'period_type': 'quarterly' if rd['type'] == 'sales_tax' else 'annual',
                        'period_start': rd['period_start'],
                        'period_end': rd['period_end'],
                        'due_date': rd['due_date'],
                        'status': rd['status'],
                        'total_taxable_amount': rd['taxable'],
                        'total_tax_due': rd['tax_due'],
                        'net_tax_due': rd['net_due'],
                        'amount_paid': rd['paid'],
                        'created_by': user,
                        'filed_date': rd['due_date'] if rd['status'] == 'filed' else None,
                        'filed_by': user if rd['status'] == 'filed' else None,
                    }
                )
                if created:
                    TaxReturnLine.objects.create(
                        tax_return=tr, line_number=1,
                        description='Gross Sales',
                        taxable_amount=rd['taxable'],
                        tax_amount=rd['tax_due'],
                        rate_applied=Decimal('7.25000') if rd['type'] == 'sales_tax' else Decimal('21.00000'),
                    )

            # =================================================================
            # 6. Tax Deadlines
            # =================================================================
            deadlines_data = [
                {'name': 'CA Sales Tax Q1 2026', 'type': 'sales_tax', 'jurisdiction': 'US-CA',
                 'due': date(2026, 4, 30), 'status': 'upcoming', 'recurring': True, 'pattern': 'quarterly'},
                {'name': 'NY Sales Tax Q1 2026', 'type': 'sales_tax', 'jurisdiction': 'US-NY',
                 'due': date(2026, 4, 20), 'status': 'in_progress', 'recurring': True, 'pattern': 'quarterly'},
                {'name': 'Federal Income Tax 2025', 'type': 'income_tax', 'jurisdiction': 'US-FED',
                 'due': date(2026, 4, 15), 'status': 'upcoming', 'recurring': True, 'pattern': 'annual'},
                {'name': 'TX Sales Tax Monthly Mar 2026', 'type': 'sales_tax', 'jurisdiction': 'US-TX',
                 'due': date(2026, 4, 20), 'status': 'upcoming', 'recurring': True, 'pattern': 'monthly'},
                {'name': 'CA Property Tax 2025-2026', 'type': 'property_tax', 'jurisdiction': 'US-CA',
                 'due': date(2026, 4, 10), 'status': 'upcoming', 'recurring': False, 'pattern': ''},
            ]

            for dd in deadlines_data:
                j = created_jurisdictions.get(dd['jurisdiction'])
                if not j:
                    continue
                TaxDeadline.unscoped.get_or_create(
                    tenant=tenant,
                    deadline_number=TaxDeadline.generate_deadline_number(tenant),
                    defaults={
                        'name': dd['name'],
                        'tax_type': dd['type'],
                        'jurisdiction': j,
                        'due_date': dd['due'],
                        'status': dd['status'],
                        'reminder_days': 7,
                        'is_recurring': dd['recurring'],
                        'recurrence_pattern': dd['pattern'],
                    }
                )

            # =================================================================
            # 7. Nexus Tracking
            # =================================================================
            nexus_data = [
                {'jurisdiction': 'US-CA', 'type': 'economic', 'has_nexus': True,
                 'reg_status': 'registered', 'reg_number': 'CA-ST-1234567',
                 'threshold_amt': Decimal('500000.00'), 'threshold_txn': 200,
                 'sales': Decimal('620000.00'), 'txns': 450},
                {'jurisdiction': 'US-NY', 'type': 'economic', 'has_nexus': True,
                 'reg_status': 'registered', 'reg_number': 'NY-ST-9876543',
                 'threshold_amt': Decimal('500000.00'), 'threshold_txn': 100,
                 'sales': Decimal('380000.00'), 'txns': 120},
                {'jurisdiction': 'US-TX', 'type': 'economic', 'has_nexus': False,
                 'reg_status': 'not_required', 'reg_number': '',
                 'threshold_amt': Decimal('500000.00'), 'threshold_txn': 200,
                 'sales': Decimal('85000.00'), 'txns': 45},
            ]

            for nd in nexus_data:
                j = created_jurisdictions.get(nd['jurisdiction'])
                if not j:
                    continue
                nj, created = NexusJurisdiction.unscoped.get_or_create(
                    tenant=tenant, jurisdiction=j, nexus_type=nd['type'],
                    defaults={
                        'has_nexus': nd['has_nexus'],
                        'registration_status': nd['reg_status'],
                        'registration_number': nd['reg_number'],
                        'registration_date': date(2025, 1, 1) if nd['reg_status'] == 'registered' else None,
                        'economic_threshold_amount': nd['threshold_amt'],
                        'economic_threshold_transactions': nd['threshold_txn'],
                        'current_period_sales': nd['sales'],
                        'current_period_transactions': nd['txns'],
                        'threshold_percentage': max(
                            (nd['sales'] / nd['threshold_amt'] * 100).quantize(Decimal('0.01')) if nd['threshold_amt'] else Decimal('0'),
                            Decimal(nd['txns'] / nd['threshold_txn'] * 100).quantize(Decimal('0.01')) if nd['threshold_txn'] else Decimal('0'),
                        ),
                        'is_active': True,
                    }
                )
                if created:
                    NexusActivity.unscoped.create(
                        tenant=tenant,
                        nexus_jurisdiction=nj,
                        period_start=date(2026, 1, 1),
                        period_end=date(2026, 3, 31),
                        sales_amount=nd['sales'],
                        transaction_count=nd['txns'],
                    )

        self.stdout.write(
            f'  Created TX data (jurisdictions, tax rates, tax rules, '
            f'tax groups, tax returns, deadlines, nexus tracking)'
        )
