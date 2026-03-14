# NavAccounting

A comprehensive multi-tenant accounting application built with Django 5.1 and Bootstrap 5.3. Designed for small-to-medium businesses with support for multiple organizations, role-based access control, and a modern responsive dashboard.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Seeding Data](#seeding-data)
- [Default Credentials](#default-credentials)
- [Multi-Tenancy Architecture](#multi-tenancy-architecture)
- [Authentication](#authentication)
- [URL Routing](#url-routing)
- [Django Apps](#django-apps)
- [Frontend & Theming](#frontend--theming)
- [Role-Based Access Control](#role-based-access-control)
- [Future Modules](#future-modules)

---

## Features

- **Multi-Tenant Architecture** — Shared-schema with URL-based tenant resolution and automatic data isolation
- **Dashboard & Analytics** — KPI cards, cash flow charts, alert center, quick actions, executive summary
- **User Management** — Registration, login, forgot password, email verification, user invitation system
- **Role-Based Access Control** — Permissions, roles, and tenant-level user role assignment
- **Company Setup** — Company settings, fiscal years, fiscal periods, currency management
- **Chart of Accounts** — Pre-built COA templates with hierarchical account structure, template import to tenant accounts
- **General Ledger** — Double-entry journal entries, approval workflows, period close, reconciliation, allocations, audit trail, multi-currency exchange rates
- **Accounts Payable** — Vendor management, bill capture & processing, payment processing & batching, payment scheduling, aging reports, vendor portal, early payment discounts
- **Accounts Receivable** — Customer management, invoice generation & approvals, payment collection (receipts), recurring invoicing, cash application, collections & dunning, credit management, aging analysis, customer portal
- **Cash Management** — Bank account management, bank feeds, transaction import (CSV), bank reconciliation with auto-match, cash positioning dashboard, treasury forecasting, intercompany transfers with GL integration, bank fee analysis
- **Fixed Assets** — Asset register with categories & locations, acquisition tracking (purchase/lease/donation/CIP), depreciation engine (straight-line, declining balance, units of production), asset transfers with approval workflow, disposals & retirements (sale/scrap/write-off with gain/loss GL posting), impairment testing, physical inventory with barcode scanning & reconciliation, tax depreciation books (MACRS/bonus/Section 179)
- **Inventory & Cost Management** — Item master with categories, units of measure & warehouses, purchase requisitions with PO conversion, purchase orders with approval workflow, goods receipts with cost layer creation, inventory transactions (adjustments/scrap), inter-warehouse transfers, COGS calculation engine (FIFO/LIFO/weighted average/standard), inventory valuation report, reorder point planning with auto-PO generation, cycle counting with variance GL posting, landed cost allocation with GL integration
- **Payroll Integration** — Employee master with pay types (salary/hourly) and frequencies, payroll journal with calculate/approve/post workflow, tax withholding configuration (federal/state/local/FICA/FUTA/SUTA), tax remittance tracking, benefit plans (401k/health/dental/vision/HSA/FSA) with employee enrollment, court-ordered garnishment management with priority ordering, workers comp class assignments with rate tracking, gross-to-net payroll reconciliation with variance detection, GL journal entry posting
- **Project/Job Costing** — Project master with WBS hierarchy, time & expense tracking, billing rules with markup, revenue recognition (percentage-of-completion/milestone/completed-contract), project invoicing with retention, profitability analysis with earned value metrics, resource planning & utilization reports, audit trail integration
- **Multi-Entity & Consolidation** — Entity management (parent/subsidiary/branch/division/JV/associate) with hierarchical structure, intercompany transactions with paired journal entries, IC balance reconciliation, currency translation with CTA calculation, consolidation engine with elimination rules, minority interest computation, transfer pricing policies with arm's length analysis, local GAAP adjustments, regulatory report filing
- **Tax Management** — Sales tax engine with hierarchical jurisdictions, effective-dated rates, compound rate calculation, product taxability rules & tax groups; tax return preparation (Sales Tax/VAT/GST/Income Tax) with Draft→Calculated→Reviewed→Filed workflow; use tax self-assessment tracking with GL accrual posting; income tax provision with current/deferred tax, temporary differences, and ETR reconciliation; tax calendar with filing deadline management, recurring deadline generation & overdue alerts; audit support with findings tracking, document repository & adjustment GL posting; economic nexus monitoring with threshold tracking, progress alerts & registration management
- **Theme System** — Light/dark mode, 3 layout variants (vertical/horizontal/detached), RTL support, sidebar customization
- **Responsive Design** — Fully responsive Bootstrap 5.3 interface
- **Seed Data** — Management command to populate fake data for development and testing

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5.1, Python 3.11 |
| Frontend | Bootstrap 5.3, ApexCharts, Bootstrap Icons |
| Database | MySQL / MariaDB (custom backend for MariaDB 10.4+ compatibility) |
| Authentication | django-allauth (email-based login) |
| Forms | django-crispy-forms + crispy-bootstrap5, django-widget-tweaks |
| Static Files | WhiteNoise |
| Fake Data | Faker |
| Dev Tools | django-debug-toolbar, django-extensions |

---

## Project Structure

```
NavAccounting/
├── manage.py                       # Django management entry point
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (DB, secrets)
├── .gitignore
├── navaccounting/                  # Django project package
│   ├── settings/
│   │   ├── __init__.py             # Auto-detects dev/prod from DEBUG
│   │   ├── base.py                 # Shared settings (apps, middleware, allauth)
│   │   ├── development.py          # MySQL config, debug toolbar
│   │   └── production.py           # Production security settings
│   ├── db_backends/
│   │   └── mysql/                  # Custom MySQL backend for MariaDB 10.4
│   │       ├── base.py             # DatabaseWrapper override
│   │       └── features.py         # Version check & RETURNING clause fix
│   ├── urls.py                     # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/                       # Abstract models, template tags, seeders
│   ├── tenants/                    # Tenant model, middleware, managers
│   ├── accounts/                   # CustomUser, UserProfile, UserInvitation
│   ├── roles/                      # Permission, Role, TenantUserRole
│   ├── company/                    # CompanySettings, FiscalYear, Currency, COA
│   ├── general_ledger/             # COA, Journal Entries, Approvals, Period Close, Reconciliation, Allocations, Audit Trail, Exchange Rates
│   ├── accounts_payable/           # Vendors, Bills, Payments, Batches, Uploads, Scheduling, Aging, Vendor Portal
│   ├── accounts_receivable/        # Customers, Invoices, Receipts, Recurring, Cash Application, Collections, Credit Memos, Aging, Customer Portal
│   ├── cash_management/            # Bank Accounts, Feeds, Transactions, Reconciliation, Cash Position, Forecasts, Transfers, Bank Fees
│   ├── fixed_assets/               # Asset Register, Acquisitions, Depreciation, Transfers, Disposals, Impairment, Inventory, Tax Books
│   ├── inventory/                  # Item Master, Purchasing, Goods Receipts, Transactions, Transfers, COGS, Reorder Planning, Cycle Counts, Landed Cost
│   ├── payroll/                    # Employees, Payroll Journals, Tax Withholding, Tax Remittance, Benefits, Garnishments, Workers Comp, Reconciliation
│   ├── project_costing/            # Projects, WBS, Budgets, Billing Rules, Time Entries, Expenses, Revenue Recognition, Invoices, Profitability, Resources
│   ├── multi_entity/               # Entities, IC Transactions, Currency Translation, Consolidation, Transfer Pricing, Regulatory Reporting
│   ├── tax/                        # Jurisdictions, Tax Rates, Rules, Groups, Returns, Use Tax, Provisions, Calendar, Audits, Nexus Tracking
│   └── dashboard/                  # Widget config, Alerts, KPI services
├── templates/
│   ├── base.html                   # Root HTML template
│   ├── layouts/                    # vertical, horizontal, detached
│   ├── partials/                   # _topbar, _sidebar, _footer, _preloader, etc.
│   ├── accounts/                   # Login, register, forgot password, profile
│   ├── dashboard/                  # Dashboard index + widget partials
│   ├── company/                    # Company setup, fiscal years, COA
│   ├── general_ledger/             # GL templates (18 files across 7 subdirectories)
│   │   ├── chart_of_accounts/      # Account list, form, import template
│   │   ├── journal_entries/        # Journal list, form, detail
│   │   ├── approvals/              # Approval queue, detail
│   │   ├── period_close/           # Period list, detail with checklist
│   │   ├── reconciliation/         # Reconciliation list, form
│   │   ├── allocation/             # Allocation list, form
│   │   ├── audit_trail/            # Audit log list
│   │   └── currency/               # Exchange rate list, form
│   ├── accounts_payable/           # AP templates (29 files across 9 subdirectories)
│   │   ├── vendors/                # Vendor list, form, detail
│   │   ├── payment_terms/          # Payment term list, form
│   │   ├── bills/                  # Bill list, form, detail, approval queue
│   │   ├── payments/               # Payment list, form, detail
│   │   ├── batches/                # Batch list, form, detail
│   │   ├── uploads/                # Upload list, form, detail
│   │   ├── schedule/               # Schedule list, form
│   │   ├── reports/                # Aging summary, aging detail, discount opportunities
│   │   └── portal/                 # Portal base, login, dashboard, bill detail, messages
│   ├── accounts_receivable/        # AR templates (31 files across 10 subdirectories)
│   │   ├── customers/              # Customer list, form, detail
│   │   ├── invoices/               # Invoice list, form, detail, approval queue
│   │   ├── receipts/               # Receipt list, form, detail
│   │   ├── recurring/              # Recurring template list, form, detail
│   │   ├── credit_memos/           # Credit memo list, form, detail
│   │   ├── collections/            # Dashboard, customer detail, activity form, activity list
│   │   ├── cash_application/       # Cash application interface
│   │   ├── reports/                # AR aging summary, aging detail
│   │   └── portal/                 # Portal base, login, dashboard, invoice list/detail, payment, messages
│   ├── cash_management/            # CM templates (23 files across 7 subdirectories)
│   │   ├── bank_accounts/          # Bank account list, form, detail
│   │   ├── bank_feeds/             # Bank feed list, form
│   │   ├── transactions/           # Transaction list, import, detail
│   │   ├── reconciliation/         # Reconciliation list, start, workspace, match rule list/form
│   │   ├── cash_position/          # Cash position dashboard
│   │   ├── forecasts/              # Forecast list, form, detail
│   │   ├── transfers/              # Transfer list, form, detail
│   │   └── bank_fees/              # Fee list, form, analysis dashboard
│   ├── fixed_assets/               # FA templates (20 files across 9 subdirectories)
│   │   ├── assets/                 # Asset list, create, detail, edit
│   │   ├── categories/             # Category list, form
│   │   ├── locations/              # Location list, form
│   │   ├── acquisitions/           # Acquisition list, form
│   │   ├── depreciation/           # Depreciation dashboard, run depreciation, schedule detail
│   │   ├── transfers/              # Transfer list, form
│   │   ├── disposals/              # Disposal list, form
│   │   ├── impairment/             # Impairment list, form
│   │   ├── inventory/              # Inventory list, form, count
│   │   └── tax_depreciation/       # Tax book list, book detail
│   ├── inventory/                  # IC templates (39 files across 14 subdirectories)
│   │   ├── items/                  # Item list, create, detail, edit
│   │   ├── categories/             # Category list, form
│   │   ├── uom/                    # Unit of measure list, form
│   │   ├── warehouses/             # Warehouse list, form
│   │   ├── requisitions/           # Requisition list, form, detail
│   │   ├── purchase_orders/        # PO list, form, detail
│   │   ├── goods_receipts/         # Receipt list, form, detail
│   │   ├── transactions/           # Transaction list, adjustment form, scrap form
│   │   ├── transfers/              # Transfer list, form, detail
│   │   ├── cogs/                   # COGS dashboard, calculate, detail
│   │   ├── valuation/              # Valuation report
│   │   ├── reorder/                # Reorder dashboard
│   │   ├── cycle_counts/           # Plan list, plan form, session list, session form, session detail, count form
│   │   └── landed_cost/            # Landed cost list, form, detail
│   ├── payroll/                    # PR templates (22 files across 7 subdirectories)
│   │   ├── employees/              # Employee list, form, detail
│   │   ├── payroll_journal/        # Journal list, form, detail
│   │   ├── tax_management/         # Withholding list, form, remittance list, form, detail
│   │   ├── benefits/               # Benefit plan list, form, detail, enrollment form
│   │   ├── garnishments/           # Garnishment list, form, detail
│   │   ├── workers_comp/           # Comp class list, form, detail, assignment form
│   │   └── reconciliation/         # Reconciliation list, form, detail
│   ├── project_costing/            # PJ templates (34 files across 11 subdirectories)
│   │   ├── projects/               # Project list, form, detail
│   │   ├── wbs/                    # WBS list, form, confirm delete
│   │   ├── budgets/                # Budget list, form, confirm delete
│   │   ├── billing_rules/          # Billing rule list, form, confirm delete
│   │   ├── time_entries/           # Time entry list, form, confirm delete
│   │   ├── expenses/               # Expense list, form, confirm delete
│   │   ├── revenue_recognition/    # Revenue recognition list, form, detail
│   │   ├── milestones/             # Milestone list, form
│   │   ├── invoices/               # Invoice list, form, detail
│   │   ├── profitability/          # Dashboard, detail, snapshot form, snapshot list
│   │   └── resources/              # Assignment list, form, confirm delete, utilization report
│   ├── multi_entity/               # ME templates (30 files across 6 subdirectories)
│   │   ├── entities/               # Entity list, form, detail, hierarchy
│   │   ├── intercompany/           # IC transaction list, form, detail, balance list
│   │   ├── translation/            # Translation rule list, form, run, adjustment list, detail
│   │   ├── consolidation/          # Group list, form, detail, elimination rule list, form, run list, form, detail
│   │   ├── transfer_pricing/       # TP policy list, form, detail, transaction list, form
│   │   └── regulatory/             # GAAP adjustment list, form, detail, report list, form, detail
│   ├── tax/                        # TX templates (40 files across 7 subdirectories)
│   │   ├── sales_tax/              # Jurisdiction list, form, detail, tax rate list, form, tax rule list, form, tax group list, form, detail
│   │   ├── tax_returns/            # Return list, form, detail, payment form, line form
│   │   ├── use_tax/                # Assessment list, form, detail, accrual list, form, detail
│   │   ├── provision/              # Provision list, form, detail, edit (with deferred items & ETR formsets)
│   │   ├── calendar/               # Deadline list, form, detail, generate recurring form
│   │   ├── audit/                  # Audit list, form, detail, finding form, finding edit, document upload
│   │   └── nexus/                  # Nexus list, form, detail, activity form, dashboard
│   ├── roles/                      # Role list, role form, assign
│   └── tenants/                    # Tenant select, create
├── static/
│   ├── css/                        # theme-variables, app, layouts, dark-mode, rtl
│   ├── js/                         # layout, theme, sidebar, topbar, dashboard-charts
│   └── images/                     # Logos, avatars, backgrounds
└── media/                          # User-uploaded files
```

---

## Installation

### Prerequisites

- Python 3.10+
- MySQL 8.0+ or MariaDB 10.4+ (XAMPP included)
- pip (Python package manager)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/NavAccounting.git
cd NavAccounting

# 2. Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy or edit the `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production-navaccounting-2026
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Database
DB_ENGINE=navaccounting.db_backends.mysql
DB_NAME=navaccounting
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

### Settings Structure

| File | Purpose |
|------|---------|
| `settings/base.py` | Shared config — installed apps, middleware, allauth, templates |
| `settings/development.py` | `DEBUG=True`, MySQL, debug toolbar, console email |
| `settings/production.py` | Security hardening, production database |
| `settings/__init__.py` | Auto-selects dev or prod based on `DEBUG` env var |

---

## Database Setup

### Using XAMPP (MariaDB)

1. Start **Apache** and **MySQL** from XAMPP Control Panel
2. Create the database:

```sql
CREATE DATABASE navaccounting CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Run migrations:

```bash
python manage.py migrate
```

### MariaDB 10.4 Compatibility

Django 5.1 officially requires MariaDB 10.5+. This project includes a **custom database backend** (`navaccounting/db_backends/mysql/`) that:
- Lowers the minimum MariaDB version requirement to 10.4
- Disables `INSERT ... RETURNING` syntax for MariaDB versions below 10.5

No additional configuration is needed — the custom backend is used automatically via the `DB_ENGINE` setting.

---

## Running the Application

```bash
# Start the development server
python manage.py runserver

# Or specify a port
python manage.py runserver 8000
```

Visit: [http://localhost:8000](http://localhost:8000)

---

## Seeding Data

Populate the database with sample data for development:

```bash
# Seed everything
python manage.py seed_data

# Clean and re-seed (wipes existing data first)
python manage.py seed_data --clean

# Seed specific categories
python manage.py seed_data --tenants
python manage.py seed_data --users
python manage.py seed_data --company
python manage.py seed_data --coa
python manage.py seed_data --dashboard
python manage.py seed_data --gl
python manage.py seed_data --ap
python manage.py seed_data --ar
python manage.py seed_data --cm
python manage.py seed_data --fa
python manage.py seed_data --ic
python manage.py seed_data --pj
python manage.py seed_data --me
python manage.py seed_data --tx
```

### What Gets Seeded

| Category | Data |
|----------|------|
| Currencies | 30 currencies (USD, EUR, GBP, JPY, etc.) with ISO 4217 codes |
| Account Types | 5 types — Asset, Liability, Equity, Revenue, Expense |
| Permissions | 46 module-based permissions (view/manage dashboard, users, roles, GL, AP, AR, CM, etc.) |
| COA Template | "Standard Business" template with 61 hierarchical accounts |
| Tenants | 3 organizations — Acme Corporation, TechStart Solutions, Green Valley Farms |
| Users | Superuser + 10 users per tenant (managers, accountants, viewers) |
| Roles | 4 system roles per tenant — Admin, Manager, Accountant, Viewer |
| Company Settings | Company info, fiscal years (2025-2026), 12 monthly periods |
| Dashboard | 12 alerts + 5 widget configurations per tenant |
| General Ledger | COA imported from template, 3 exchange rates, 3 sample posted journal entries per tenant |
| Accounts Payable | 7 payment terms, 5 vendors with contacts, 5 bills with line items, 1 completed payment with allocation, 1 vendor portal token |
| Accounts Receivable | 5 customers with contacts, 6 invoices with line items, 2 receipts with allocations, 1 recurring invoice template, 2 collection activities, 1 customer portal token |
| Cash Management | 2 bank accounts with signatories, 2 bank feeds, 15 transactions, 2 auto-match rules, 1 forecast with 10 lines, 2 intercompany transfers, 8 bank fees |
| Fixed Assets | 5 asset categories (BLDG, VEHI, FURN, COMP, MACH), 3 locations (HQ, WH1, BR1), 8 assets with depreciation profiles and schedules, 4 acquisitions, 1 asset transfer, 1 MACRS tax book with entries, 1 physical inventory with items |
| Inventory & Cost | 5 item categories (RAW, FG, COMP, PKG, MRO), 5 UoMs, 3 warehouses, 8 items with cost layers, 1 purchase requisition, 2 purchase orders with lines, 1 posted goods receipt, 2 inventory transactions (adjustment + scrap), 1 completed transfer, 1 COGS calculation with entries, 3 reorder suggestions, 1 cycle count plan + session with items, 1 landed cost voucher with cost lines and allocations |
| Project/Job Costing | 5 projects (Corporate HQ Renovation, ERP Implementation, Highway Bridge Repair, Mobile App Development, Warehouse Automation), WBS elements with hierarchical structure, project budgets with GL accounts, billing rules, time entries, expense entries with markup, revenue recognition records, milestones, project invoices with lines, profitability snapshots, resource assignments |
| Multi-Entity & Consolidation | 5 entities (HQ parent, EU subsidiary, UK branch, Asia JV, US division), 8 IC transactions with varied statuses, 5 IC balances, 5 currency translation rules, 3 CTA translation adjustments, 2 consolidation groups (Global + EU sub-group), 4 elimination rules, 3 consolidation runs (completed/draft/reversed), 2 elimination entries, 2 minority interest records, 4 transfer pricing policies, 5 TP transactions, 5 GAAP adjustments, 6 regulatory reports |
| Tax Management | 7 jurisdictions (Federal, 3 states, 2 counties, 1 city) with hierarchy, 7 tax rates (CA/NY/TX/Federal), 8 tax rules (exemptions/reduced/zero-rated/surtax), 4 tax groups (CA+LA, CA+SF, NY+NYC, CA full combined), 5 tax returns with line items (filed/draft/calculated/reviewed), 5 use tax assessments (pending/accrued/paid/exempt), 2 use tax accruals (posted/draft), 3 income tax provisions with deferred items and ETR reconciliation (finalized/draft/calculated), 5 tax deadlines (recurring/one-time), 4 tax audits with findings (closed/in-progress/pending), 4 nexus jurisdictions with activity records |

---

## Default Credentials

| User | Email | Password | Role |
|------|-------|----------|------|
| Superuser | `admin@navaccounting.com` | `admin123!` | Full access to all tenants |
| Other users | Faker-generated emails | `password123!` | Varies by tenant |

---

## Multi-Tenancy Architecture

NavAccounting uses a **shared-schema, URL-based multi-tenancy** approach:

### Tenant Resolution Order

1. **URL path** — `/t/<tenant_slug>/...` (primary method)
2. **Session** — `request.session['tenant_id']` (fallback)
3. **User default** — User's default `TenantMembership` (last resort)

### Data Isolation

- All tenant-scoped models extend `TenantAwareModel` (abstract base)
- `TenantAwareManager` auto-filters all queries by the current tenant
- Tenant context stored in `threading.local()`, set by `TenantMiddleware`
- Cross-tenant access available via `Model.unscoped.all()` (explicit opt-in)

### Tenant-Free Routes

These paths skip tenant resolution:
- `/auth/` — Login, registration, password reset
- `/admin/` — Django admin (superusers only)
- `/tenants/` — Tenant selection and creation
- `/vendor-portal/` — Vendor portal (token-based auth, no Django user required)
- `/customer-portal/` — Customer portal (token-based auth, no Django user required)
- `/static/`, `/media/` — Static assets

### System-Wide vs Tenant-Scoped Models

| System-Wide (no tenant) | Tenant-Scoped |
|--------------------------|---------------|
| CustomUser | UserProfile, UserInvitation |
| Tenant, TenantMembership | CompanySettings, FiscalYear, FiscalPeriod |
| Currency, AccountType | Role, TenantUserRole |
| Permission | DashboardWidgetConfig, Alert |
| ChartOfAccountsTemplate | Account, JournalEntry, JournalEntryLine |
| — | JournalApproval, PeriodCloseChecklist |
| — | AccountReconciliation, AllocationRule, AllocationRuleLine |
| — | AuditTrail, ExchangeRate |
| — | PaymentTerm, Vendor, Bill, BillApproval, BillUpload |
| — | Payment, PaymentBatch, ScheduledPayment |
| — | VendorPortalToken, VendorMessage |
| — | Customer, CustomerContact, Invoice, InvoiceLine |
| — | InvoiceApproval, Receipt, ReceiptAllocation |
| — | RecurringInvoiceTemplate, RecurringInvoiceTemplateLine |
| — | CreditMemo, CollectionActivity, WriteOff |
| — | CustomerPortalToken, CustomerMessage |
| — | BankAccount, BankAccountSignatory, BankFeed |
| — | BankTransaction, BankReconciliation, ReconciliationItem |
| — | AutoMatchRule, CashForecast, CashForecastLine |
| — | IntercompanyTransfer, BankFee |
| — | AssetCategory, AssetLocation, Asset |
| — | AssetAcquisition, DepreciationProfile, DepreciationSchedule |
| — | DepreciationEntry, AssetTransfer, AssetDisposal |
| — | ImpairmentTest, PhysicalInventory, TaxDepreciationBook |
| — | TaxDepreciationEntry |
| — | ItemCategory, UnitOfMeasure, Item, CostLayer |
| — | Warehouse, PurchaseRequisition, PurchaseRequisitionLine |
| — | PurchaseOrder, PurchaseOrderLine |
| — | GoodsReceipt, GoodsReceiptLine |
| — | InventoryTransaction, InventoryTransfer, InventoryTransferLine |
| — | COGSCalculation, COGSEntry, ReorderSuggestion |
| — | CycleCountPlan, CycleCountSession, CycleCountItem |
| — | LandedCostVoucher, LandedCostLine, LandedCostAllocation |
| — | Employee, PayrollJournal, TaxWithholding, TaxRemittance |
| — | BenefitPlan, Garnishment, WorkersCompClass |
| — | PayrollReconciliation |
| — | Project, WBSElement, ProjectBudget, BillingRule |
| — | TimeEntry, ExpenseEntry, RevenueRecognition |
| — | ProjectMilestone, ProjectInvoice, ProjectInvoiceLine |
| — | ProfitabilitySnapshot, ResourceAssignment |
| — | Entity, IntercompanyTransaction, IntercompanyBalance |
| — | CurrencyTranslationRule, TranslationAdjustment |
| — | ConsolidationGroup, ConsolidationRun, EliminationRule |
| — | EliminationEntry, MinorityInterest |
| — | TransferPricingPolicy, TransferPricingTransaction |
| — | LocalGAAPAdjustment, RegulatoryReport |
| — | TaxJurisdiction, TaxRate, TaxRule, TaxGroup |
| — | TaxReturn, TaxReturnLine, TaxReturnPayment |
| — | UseTaxAssessment, UseTaxAccrual |
| — | IncomeTaxProvision, DeferredTaxItem, ETRReconciliation |
| — | TaxDeadline, TaxDeadlineReminder |
| — | TaxAudit, AuditFinding, AuditDocument |
| — | NexusJurisdiction, NexusActivity |

---

## Authentication

Powered by **django-allauth** with custom configuration:

| Setting | Value |
|---------|-------|
| Login method | Email (not username) |
| Email verification | Optional |
| Rate limiting | 5 failed logins per 5 minutes |
| Session duration | 14 days |
| Post-login redirect | `/tenants/select/` |
| Post-signup redirect | `/tenants/select/` |

### Auth Pages

| Page | URL |
|------|-----|
| Login | `/auth/login/` |
| Register | `/auth/register/` |
| Forgot Password | `/auth/forgot-password/` |
| Reset Password | `/auth/password/reset/key/<token>/` |
| Email Verification | `/auth/confirm-email/<key>/` |
| Accept Invitation | `/auth/accept-invite/<uuid:token>/` |
| Logout | `/auth/logout/` |

### Custom Adapter

On user registration, the `NavAccountingAdapter` automatically:
1. Creates a default `Tenant` for the user
2. Creates a `TenantMembership` marked as default
3. Sets the user's `last_active_tenant`

---

## URL Routing

### Root URLs

| Pattern | Destination |
|---------|-------------|
| `/admin/` | Django admin panel |
| `/auth/` | Authentication (login, register, forgot password) |
| `/tenants/` | Tenant management (select, create, switch) |
| `/t/<slug>/` | Tenant-scoped routes (dashboard, company, users, roles, GL, AP, AR, CM, FA, IC, PR, PJ, ME, TX) |
| `/vendor-portal/` | Vendor portal (token-based, no login required) |
| `/customer-portal/` | Customer portal (token-based, no login required) |
| `/` | Redirects to tenant select or login |

### Tenant-Scoped URLs (`/t/<tenant_slug>/...`)

| Pattern | View | Description |
|---------|------|-------------|
| `/t/<slug>/` | Dashboard index | KPI cards, charts, alerts |
| `/t/<slug>/company/setup/` | Company setup | Company details form |
| `/t/<slug>/company/fiscal-years/` | Fiscal year list | View/manage fiscal years |
| `/t/<slug>/company/fiscal-years/create/` | Create fiscal year | New fiscal year form |
| `/t/<slug>/company/fiscal-years/<pk>/edit/` | Edit fiscal year | Edit fiscal year form |
| `/t/<slug>/company/currencies/` | Currency settings | Manage currencies |
| `/t/<slug>/company/coa-templates/` | COA templates | Chart of accounts templates |
| `/t/<slug>/company/coa-templates/<pk>/` | COA template detail | View template accounts |
| `/t/<slug>/users/` | User list | Manage tenant users |
| `/t/<slug>/users/invite/` | Invite user | Send invitation email |
| `/t/<slug>/users/profile/` | User profile | Edit current user profile |
| `/t/<slug>/roles/` | Role list | View/manage roles |
| `/t/<slug>/roles/create/` | Create role | New role form |
| `/t/<slug>/roles/<pk>/edit/` | Edit role | Edit role permissions |
| `/t/<slug>/roles/assign/` | Assign role | Assign role to user |
| `/t/<slug>/gl/accounts/` | Account list | Chart of accounts (tree view) |
| `/t/<slug>/gl/accounts/create/` | Create account | New GL account form |
| `/t/<slug>/gl/accounts/<pk>/edit/` | Edit account | Edit GL account |
| `/t/<slug>/gl/accounts/<pk>/delete/` | Delete account | Delete GL account |
| `/t/<slug>/gl/accounts/import-template/` | Import template | Import COA from template |
| `/t/<slug>/gl/journal/` | Journal list | All journal entries |
| `/t/<slug>/gl/journal/create/` | Create journal | New journal entry with lines |
| `/t/<slug>/gl/journal/<pk>/` | Journal detail | View entry detail + approval history |
| `/t/<slug>/gl/journal/<pk>/edit/` | Edit journal | Edit draft journal entry |
| `/t/<slug>/gl/journal/<pk>/submit/` | Submit journal | Submit entry for approval |
| `/t/<slug>/gl/journal/<pk>/post/` | Post journal | Post approved entry |
| `/t/<slug>/gl/approvals/` | Approval queue | Pending entries for approval |
| `/t/<slug>/gl/approvals/<pk>/` | Approval detail | Review entry + approve/reject |
| `/t/<slug>/gl/period-close/` | Period close list | Fiscal periods with close status |
| `/t/<slug>/gl/period-close/<pk>/` | Period close detail | Checklist + close/reopen actions |
| `/t/<slug>/gl/reconciliation/` | Reconciliation list | Account reconciliations |
| `/t/<slug>/gl/reconciliation/create/` | Create reconciliation | New reconciliation |
| `/t/<slug>/gl/reconciliation/<pk>/` | Reconciliation form | Reconcile account balance |
| `/t/<slug>/gl/allocations/` | Allocation list | Cost allocation rules |
| `/t/<slug>/gl/allocations/create/` | Create allocation | New allocation rule |
| `/t/<slug>/gl/allocations/<pk>/edit/` | Edit allocation | Edit allocation rule |
| `/t/<slug>/gl/allocations/<pk>/run/` | Run allocation | Execute allocation (creates JE) |
| `/t/<slug>/gl/exchange-rates/` | Exchange rate list | Currency exchange rates |
| `/t/<slug>/gl/exchange-rates/create/` | Create rate | New exchange rate |
| `/t/<slug>/gl/exchange-rates/<pk>/edit/` | Edit rate | Edit exchange rate |
| `/t/<slug>/gl/audit-trail/` | Audit trail | Immutable audit log |
| **Accounts Payable — Vendors** | | |
| `/t/<slug>/ap/vendors/` | Vendor list | All vendors with filters |
| `/t/<slug>/ap/vendors/create/` | Create vendor | New vendor form with contacts |
| `/t/<slug>/ap/vendors/<pk>/` | Vendor detail | Vendor info, bills, payments |
| `/t/<slug>/ap/vendors/<pk>/edit/` | Edit vendor | Edit vendor details |
| `/t/<slug>/ap/vendors/<pk>/toggle-active/` | Toggle active | Activate/deactivate vendor |
| `/t/<slug>/ap/payment-terms/` | Payment term list | All payment terms |
| `/t/<slug>/ap/payment-terms/create/` | Create payment term | New term form |
| `/t/<slug>/ap/payment-terms/<pk>/edit/` | Edit payment term | Edit term details |
| **Accounts Payable — Bills** | | |
| `/t/<slug>/ap/bills/` | Bill list | All bills with status filters |
| `/t/<slug>/ap/bills/create/` | Create bill | New bill with line items |
| `/t/<slug>/ap/bills/<pk>/` | Bill detail | Bill info, lines, payments |
| `/t/<slug>/ap/bills/<pk>/edit/` | Edit bill | Edit draft bill |
| `/t/<slug>/ap/bills/<pk>/submit/` | Submit bill | Submit for approval |
| `/t/<slug>/ap/bills/<pk>/void/` | Void bill | Void a bill |
| `/t/<slug>/ap/bills/approvals/` | Approval queue | Pending bills for approval |
| `/t/<slug>/ap/bills/approvals/<pk>/approve/` | Approve bill | Approve a bill |
| `/t/<slug>/ap/bills/approvals/<pk>/reject/` | Reject bill | Reject a bill |
| **Accounts Payable — Payments** | | |
| `/t/<slug>/ap/payments/` | Payment list | All payments with filters |
| `/t/<slug>/ap/payments/create/` | Create payment | New payment with allocations |
| `/t/<slug>/ap/payments/<pk>/` | Payment detail | Payment info, allocations, JE |
| `/t/<slug>/ap/payments/<pk>/complete/` | Complete payment | Mark payment completed |
| `/t/<slug>/ap/payments/<pk>/void/` | Void payment | Void a payment |
| `/t/<slug>/ap/batches/` | Batch list | Payment batches |
| `/t/<slug>/ap/batches/create/` | Create batch | New payment batch |
| `/t/<slug>/ap/batches/<pk>/` | Batch detail | Batch payments |
| `/t/<slug>/ap/batches/<pk>/process/` | Process batch | Execute batch payments |
| **Accounts Payable — Bill Capture** | | |
| `/t/<slug>/ap/uploads/` | Upload list | Bill uploads (OCR) |
| `/t/<slug>/ap/uploads/create/` | Upload bill | Upload invoice for OCR |
| `/t/<slug>/ap/uploads/<pk>/` | Upload detail | OCR results, extracted data |
| `/t/<slug>/ap/uploads/<pk>/create-bill/` | Create bill from upload | Convert upload to bill |
| **Accounts Payable — Scheduling & Reports** | | |
| `/t/<slug>/ap/schedule/` | Schedule list | Scheduled payments |
| `/t/<slug>/ap/schedule/create/` | Create schedule | Schedule a payment |
| `/t/<slug>/ap/schedule/<pk>/execute/` | Execute schedule | Execute scheduled payment |
| `/t/<slug>/ap/schedule/<pk>/cancel/` | Cancel schedule | Cancel scheduled payment |
| `/t/<slug>/ap/reports/aging/` | Aging summary | AP aging by vendor |
| `/t/<slug>/ap/reports/aging/<vendor_pk>/` | Aging detail | Vendor aging detail |
| `/t/<slug>/ap/reports/aging/export/` | Aging export | Export aging report CSV |
| `/t/<slug>/ap/reports/discounts/` | Discount opportunities | Early payment discounts |
| **Accounts Receivable — Customers** | | |
| `/t/<slug>/ar/customers/` | Customer list | All customers with filters |
| `/t/<slug>/ar/customers/create/` | Create customer | New customer form with contacts |
| `/t/<slug>/ar/customers/<pk>/` | Customer detail | Customer info, invoices, receipts |
| `/t/<slug>/ar/customers/<pk>/edit/` | Edit customer | Edit customer details |
| `/t/<slug>/ar/customers/<pk>/toggle/` | Toggle active | Activate/deactivate customer |
| `/t/<slug>/ar/customers/<pk>/credit-hold/` | Credit hold | Toggle credit hold on customer |
| **Accounts Receivable — Invoices** | | |
| `/t/<slug>/ar/invoices/` | Invoice list | All invoices with status filters |
| `/t/<slug>/ar/invoices/create/` | Create invoice | New invoice with line items |
| `/t/<slug>/ar/invoices/<pk>/` | Invoice detail | Invoice info, lines, receipts |
| `/t/<slug>/ar/invoices/<pk>/edit/` | Edit invoice | Edit draft invoice |
| `/t/<slug>/ar/invoices/<pk>/submit/` | Submit invoice | Submit for approval |
| `/t/<slug>/ar/invoices/<pk>/send/` | Send invoice | Mark invoice as sent |
| `/t/<slug>/ar/invoices/<pk>/void/` | Void invoice | Void an invoice |
| `/t/<slug>/ar/invoices/approvals/` | Approval queue | Pending invoices for approval |
| `/t/<slug>/ar/invoices/approvals/<pk>/approve/` | Approve invoice | Approve an invoice |
| `/t/<slug>/ar/invoices/approvals/<pk>/reject/` | Reject invoice | Reject an invoice |
| **Accounts Receivable — Receipts** | | |
| `/t/<slug>/ar/receipts/` | Receipt list | All receipts with filters |
| `/t/<slug>/ar/receipts/create/` | Create receipt | New receipt with allocations |
| `/t/<slug>/ar/receipts/<pk>/` | Receipt detail | Receipt info, allocations, JE |
| `/t/<slug>/ar/receipts/<pk>/complete/` | Complete receipt | Mark receipt completed |
| `/t/<slug>/ar/receipts/<pk>/void/` | Void receipt | Void a receipt |
| **Accounts Receivable — Credit Memos** | | |
| `/t/<slug>/ar/credit-memos/` | Credit memo list | All credit memos |
| `/t/<slug>/ar/credit-memos/create/` | Create credit memo | New credit memo form |
| `/t/<slug>/ar/credit-memos/<pk>/` | Credit memo detail | View credit memo details |
| `/t/<slug>/ar/credit-memos/<pk>/approve/` | Approve credit memo | Approve a credit memo |
| **Accounts Receivable — Recurring Invoicing** | | |
| `/t/<slug>/ar/recurring/` | Recurring list | All recurring templates |
| `/t/<slug>/ar/recurring/create/` | Create template | New recurring invoice template |
| `/t/<slug>/ar/recurring/<pk>/` | Template detail | View recurring template |
| `/t/<slug>/ar/recurring/<pk>/edit/` | Edit template | Edit recurring template |
| `/t/<slug>/ar/recurring/<pk>/pause/` | Pause template | Pause recurring generation |
| `/t/<slug>/ar/recurring/<pk>/cancel/` | Cancel template | Cancel recurring template |
| `/t/<slug>/ar/recurring/<pk>/generate/` | Generate invoice | Manually generate next invoice |
| **Accounts Receivable — Cash Application & Collections** | | |
| `/t/<slug>/ar/cash-application/` | Cash application | Auto-match receipts to invoices |
| `/t/<slug>/ar/cash-application/<pk>/auto-match/` | Auto-match | FIFO auto-match for a receipt |
| `/t/<slug>/ar/collections/` | Collections dashboard | Overdue invoices, dunning overview |
| `/t/<slug>/ar/collections/activities/` | Activity list | All collection activities |
| `/t/<slug>/ar/collections/<pk>/` | Customer detail | Collection detail for a customer |
| `/t/<slug>/ar/collections/<pk>/add-activity/` | Add activity | Log collection activity |
| `/t/<slug>/ar/invoices/<pk>/write-off/` | Create write-off | Write off an invoice |
| `/t/<slug>/ar/write-offs/<pk>/approve/` | Approve write-off | Approve bad debt write-off |
| **Accounts Receivable — Reports** | | |
| `/t/<slug>/ar/reports/aging/` | Aging summary | AR aging by customer |
| `/t/<slug>/ar/reports/aging/<customer_pk>/` | Aging detail | Customer aging detail |
| `/t/<slug>/ar/reports/aging/export/` | Aging export | Export aging report CSV |
| **Vendor Portal (outside tenant scope)** | | |
| `/vendor-portal/login/` | Portal login | Token-based vendor login |
| `/vendor-portal/dashboard/` | Portal dashboard | Vendor bills & payments overview |
| `/vendor-portal/bills/<pk>/` | Portal bill detail | View bill (read-only) |
| `/vendor-portal/messages/` | Portal messages | Send/receive messages |
| `/vendor-portal/messages/<pk>/` | Portal message detail | View message |
| `/vendor-portal/logout/` | Portal logout | Clear portal session |
| **Customer Portal (outside tenant scope)** | | |
| `/customer-portal/login/` | Portal login | Token-based customer login |
| `/customer-portal/dashboard/` | Portal dashboard | Customer invoices & payments overview |
| `/customer-portal/invoices/` | Portal invoice list | View all invoices |
| `/customer-portal/invoices/<pk>/` | Portal invoice detail | View invoice (read-only) |
| `/customer-portal/invoices/<pk>/pay/` | Portal make payment | Submit payment for invoice |
| `/customer-portal/messages/` | Portal messages | Send/receive messages |
| `/customer-portal/messages/<pk>/` | Portal message detail | View message |
| `/customer-portal/logout/` | Portal logout | Clear portal session |
| **Cash Management — Bank Accounts** | | |
| `/t/<slug>/cm/bank-accounts/` | Bank account list | All bank accounts with filters |
| `/t/<slug>/cm/bank-accounts/create/` | Create bank account | New bank account form with signatories |
| `/t/<slug>/cm/bank-accounts/<pk>/` | Bank account detail | Account info, transactions, reconciliations |
| `/t/<slug>/cm/bank-accounts/<pk>/edit/` | Edit bank account | Edit bank account details |
| `/t/<slug>/cm/bank-accounts/<pk>/toggle/` | Toggle active | Activate/deactivate bank account |
| **Cash Management — Bank Feeds & Transactions** | | |
| `/t/<slug>/cm/bank-feeds/` | Bank feed list | All bank feeds with status |
| `/t/<slug>/cm/bank-feeds/create/` | Create bank feed | New bank feed connection |
| `/t/<slug>/cm/bank-feeds/<pk>/edit/` | Edit bank feed | Edit bank feed settings |
| `/t/<slug>/cm/transactions/` | Transaction list | All bank transactions with filters |
| `/t/<slug>/cm/transactions/import/` | Import transactions | CSV transaction upload |
| `/t/<slug>/cm/transactions/<pk>/` | Transaction detail | Transaction info and match status |
| **Cash Management — Reconciliation** | | |
| `/t/<slug>/cm/reconciliation/` | Reconciliation list | All reconciliations with status |
| `/t/<slug>/cm/reconciliation/start/` | Start reconciliation | Select account and period |
| `/t/<slug>/cm/reconciliation/<pk>/` | Reconciliation workspace | Two-panel matching interface |
| `/t/<slug>/cm/reconciliation/<pk>/match/` | Match items | Match bank transaction to GL entry |
| `/t/<slug>/cm/reconciliation/<pk>/unmatch/` | Unmatch items | Remove a match |
| `/t/<slug>/cm/reconciliation/<pk>/auto-match/` | Auto-match | Run auto-match rules |
| `/t/<slug>/cm/reconciliation/<pk>/complete/` | Complete reconciliation | Finalize reconciliation |
| `/t/<slug>/cm/match-rules/` | Match rule list | Auto-match rules |
| `/t/<slug>/cm/match-rules/create/` | Create rule | New auto-match rule |
| `/t/<slug>/cm/match-rules/<pk>/edit/` | Edit rule | Edit auto-match rule |
| **Cash Management — Cash Position & Forecasting** | | |
| `/t/<slug>/cm/cash-position/` | Cash position | Cash position dashboard |
| `/t/<slug>/cm/forecasts/` | Forecast list | All cash forecasts |
| `/t/<slug>/cm/forecasts/create/` | Create forecast | New forecast with lines |
| `/t/<slug>/cm/forecasts/<pk>/` | Forecast detail | Forecast info with charts |
| `/t/<slug>/cm/forecasts/<pk>/edit/` | Edit forecast | Edit forecast lines |
| **Cash Management — Transfers** | | |
| `/t/<slug>/cm/transfers/` | Transfer list | All intercompany transfers |
| `/t/<slug>/cm/transfers/create/` | Create transfer | New intercompany transfer |
| `/t/<slug>/cm/transfers/<pk>/` | Transfer detail | Transfer info with actions |
| `/t/<slug>/cm/transfers/<pk>/approve/` | Approve transfer | Approve a pending transfer |
| `/t/<slug>/cm/transfers/<pk>/complete/` | Complete transfer | Complete transfer (creates GL JE) |
| `/t/<slug>/cm/transfers/<pk>/cancel/` | Cancel transfer | Cancel a transfer |
| **Cash Management — Bank Fees** | | |
| `/t/<slug>/cm/bank-fees/` | Bank fee list | All bank fees with filters |
| `/t/<slug>/cm/bank-fees/create/` | Create bank fee | New bank fee record |
| `/t/<slug>/cm/bank-fees/<pk>/edit/` | Edit bank fee | Edit bank fee details |
| `/t/<slug>/cm/bank-fees/analysis/` | Fee analysis | Bank fee analysis dashboard with charts |
| **Fixed Assets — Asset Register** | | |
| `/t/<slug>/fa/categories/` | Category list | Asset categories with GL mapping |
| `/t/<slug>/fa/categories/create/` | Create category | New asset category form |
| `/t/<slug>/fa/categories/<pk>/edit/` | Edit category | Edit asset category |
| `/t/<slug>/fa/locations/` | Location list | Asset locations |
| `/t/<slug>/fa/locations/create/` | Create location | New asset location form |
| `/t/<slug>/fa/locations/<pk>/edit/` | Edit location | Edit asset location |
| `/t/<slug>/fa/assets/` | Asset list | All assets with stat cards and filters |
| `/t/<slug>/fa/assets/create/` | Create asset | New asset form |
| `/t/<slug>/fa/assets/<pk>/` | Asset detail | Asset info, depreciation, history |
| `/t/<slug>/fa/assets/<pk>/edit/` | Edit asset | Edit asset details |
| **Fixed Assets — Acquisitions** | | |
| `/t/<slug>/fa/acquisitions/` | Acquisition list | All acquisitions with filters |
| `/t/<slug>/fa/acquisitions/create/` | Create acquisition | New acquisition form |
| `/t/<slug>/fa/acquisitions/<pk>/capitalize/` | Capitalize | Capitalize acquisition (creates GL JE) |
| **Fixed Assets — Depreciation** | | |
| `/t/<slug>/fa/depreciation/` | Depreciation dashboard | Overview with stat cards and recent entries |
| `/t/<slug>/fa/depreciation/run/` | Run depreciation | Batch depreciation run (creates GL JE) |
| `/t/<slug>/fa/depreciation/schedule/<pk>/` | Schedule detail | Asset depreciation schedule lines |
| **Fixed Assets — Transfers** | | |
| `/t/<slug>/fa/transfers/` | Transfer list | All asset transfers |
| `/t/<slug>/fa/transfers/create/` | Create transfer | New asset transfer form |
| `/t/<slug>/fa/transfers/<pk>/approve/` | Approve transfer | Approve a pending transfer |
| `/t/<slug>/fa/transfers/<pk>/complete/` | Complete transfer | Complete approved transfer |
| **Fixed Assets — Disposals** | | |
| `/t/<slug>/fa/disposals/` | Disposal list | All asset disposals |
| `/t/<slug>/fa/disposals/create/` | Create disposal | New disposal form (sale/scrap/write-off) |
| `/t/<slug>/fa/disposals/<pk>/process/` | Process disposal | Process disposal (creates GL JE with gain/loss) |
| **Fixed Assets — Impairment** | | |
| `/t/<slug>/fa/impairment/` | Impairment list | All impairment tests |
| `/t/<slug>/fa/impairment/create/` | Create impairment | New impairment test (creates GL JE if impaired) |
| **Fixed Assets — Physical Inventory** | | |
| `/t/<slug>/fa/inventory/` | Inventory list | All physical inventory counts |
| `/t/<slug>/fa/inventory/create/` | Create inventory | New inventory count (auto-populates items) |
| `/t/<slug>/fa/inventory/<pk>/count/` | Inventory count | Count items with barcode scanning |
| `/t/<slug>/fa/inventory/<pk>/reconcile/` | Reconcile | Reconcile inventory (updates asset locations) |
| **Fixed Assets — Tax Depreciation** | | |
| `/t/<slug>/fa/tax-books/` | Tax book list | Tax depreciation books |
| `/t/<slug>/fa/tax-books/create/` | Create tax book | New tax book form |
| `/t/<slug>/fa/tax-books/<pk>/` | Tax book detail | Tax book entries |
| `/t/<slug>/fa/tax-entries/create/` | Create tax entry | New tax depreciation entry |
| **Inventory & Cost — Item Master** | | |
| `/t/<slug>/ic/categories/` | Category list | Item categories |
| `/t/<slug>/ic/categories/create/` | Create category | New item category form |
| `/t/<slug>/ic/categories/<pk>/edit/` | Edit category | Edit item category |
| `/t/<slug>/ic/uom/` | UoM list | Units of measure |
| `/t/<slug>/ic/uom/create/` | Create UoM | New unit of measure form |
| `/t/<slug>/ic/uom/<pk>/edit/` | Edit UoM | Edit unit of measure |
| `/t/<slug>/ic/items/` | Item list | All items with filters |
| `/t/<slug>/ic/items/create/` | Create item | New item form |
| `/t/<slug>/ic/items/<pk>/` | Item detail | Item info, cost layers, transactions |
| `/t/<slug>/ic/items/<pk>/edit/` | Edit item | Edit item details |
| `/t/<slug>/ic/warehouses/` | Warehouse list | All warehouses |
| `/t/<slug>/ic/warehouses/create/` | Create warehouse | New warehouse form |
| `/t/<slug>/ic/warehouses/<pk>/edit/` | Edit warehouse | Edit warehouse details |
| **Inventory & Cost — Purchasing** | | |
| `/t/<slug>/ic/requisitions/` | Requisition list | Purchase requisitions |
| `/t/<slug>/ic/requisitions/create/` | Create requisition | New requisition with lines |
| `/t/<slug>/ic/requisitions/<pk>/` | Requisition detail | Requisition info and lines |
| `/t/<slug>/ic/requisitions/<pk>/approve/` | Approve requisition | Approve a requisition |
| `/t/<slug>/ic/requisitions/<pk>/convert/` | Convert to PO | Convert requisition to purchase order |
| `/t/<slug>/ic/purchase-orders/` | PO list | All purchase orders |
| `/t/<slug>/ic/purchase-orders/create/` | Create PO | New purchase order with lines |
| `/t/<slug>/ic/purchase-orders/<pk>/` | PO detail | PO info, lines, receipts |
| `/t/<slug>/ic/purchase-orders/<pk>/edit/` | Edit PO | Edit draft purchase order |
| `/t/<slug>/ic/purchase-orders/<pk>/approve/` | Approve PO | Approve a purchase order |
| `/t/<slug>/ic/goods-receipts/` | Receipt list | All goods receipts |
| `/t/<slug>/ic/goods-receipts/create/<po_pk>/` | Create receipt | New goods receipt from PO |
| `/t/<slug>/ic/goods-receipts/<pk>/` | Receipt detail | Receipt info, lines, cost layers |
| `/t/<slug>/ic/goods-receipts/<pk>/post/` | Post receipt | Post receipt (creates cost layers + GL JE) |
| **Inventory & Cost — Transactions & Transfers** | | |
| `/t/<slug>/ic/transactions/` | Transaction list | All inventory transactions |
| `/t/<slug>/ic/transactions/adjustment/` | Adjustment form | Inventory adjustment (+/-) |
| `/t/<slug>/ic/transactions/scrap/` | Scrap form | Record scrapped inventory |
| `/t/<slug>/ic/transfers/` | Transfer list | All inventory transfers |
| `/t/<slug>/ic/transfers/create/` | Create transfer | New inter-warehouse transfer |
| `/t/<slug>/ic/transfers/<pk>/` | Transfer detail | Transfer info and lines |
| `/t/<slug>/ic/transfers/<pk>/complete/` | Complete transfer | Complete transfer (creates transactions) |
| **Inventory & Cost — COGS & Valuation** | | |
| `/t/<slug>/ic/cogs/` | COGS dashboard | COGS overview with stat cards |
| `/t/<slug>/ic/cogs/calculate/` | Calculate COGS | Run COGS calculation for period |
| `/t/<slug>/ic/cogs/<pk>/` | COGS detail | Calculation detail with entries |
| `/t/<slug>/ic/cogs/<pk>/post/` | Post COGS | Post COGS to GL |
| `/t/<slug>/ic/valuation/` | Valuation report | Inventory valuation by item |
| **Inventory & Cost — Reorder Planning** | | |
| `/t/<slug>/ic/reorder/` | Reorder dashboard | Reorder suggestions with filters |
| `/t/<slug>/ic/reorder/generate/` | Generate suggestions | Scan items below reorder point |
| `/t/<slug>/ic/reorder/<pk>/approve/` | Approve suggestion | Approve a reorder suggestion |
| `/t/<slug>/ic/reorder/<pk>/dismiss/` | Dismiss suggestion | Dismiss a reorder suggestion |
| `/t/<slug>/ic/reorder/<pk>/create-po/` | Create PO | Create PO from reorder suggestion |
| **Inventory & Cost — Cycle Counting** | | |
| `/t/<slug>/ic/cycle-counts/plans/` | Plan list | Cycle count plans |
| `/t/<slug>/ic/cycle-counts/plans/create/` | Create plan | New cycle count plan |
| `/t/<slug>/ic/cycle-counts/sessions/` | Session list | Cycle count sessions |
| `/t/<slug>/ic/cycle-counts/sessions/create/` | Create session | New count session from plan |
| `/t/<slug>/ic/cycle-counts/sessions/<pk>/` | Session detail | Session info with count items |
| `/t/<slug>/ic/cycle-counts/sessions/<pk>/count/` | Enter counts | Enter physical counts |
| `/t/<slug>/ic/cycle-counts/sessions/<pk>/approve/` | Approve counts | Approve counts (posts variance adjustments) |
| **Inventory & Cost — Landed Cost** | | |
| `/t/<slug>/ic/landed-cost/` | Landed cost list | All landed cost vouchers |
| `/t/<slug>/ic/landed-cost/create/<receipt_pk>/` | Create voucher | New landed cost voucher from receipt |
| `/t/<slug>/ic/landed-cost/<pk>/` | Voucher detail | Voucher info, cost lines, allocations |
| `/t/<slug>/ic/landed-cost/<pk>/post/` | Post voucher | Post landed cost (allocates + GL JE) |
| **Payroll — Employee Master** | | |
| `/t/<slug>/pr/employees/` | Employee list | All employees with filters |
| `/t/<slug>/pr/employees/create/` | Create employee | New employee form |
| `/t/<slug>/pr/employees/<pk>/` | Employee detail | Employee info, tax, benefits, garnishments |
| `/t/<slug>/pr/employees/<pk>/edit/` | Edit employee | Edit employee details |
| **Payroll — Payroll Journal** | | |
| `/t/<slug>/pr/journals/` | Journal list | All payroll journals |
| `/t/<slug>/pr/journals/create/` | Create journal | New payroll journal with employee lines |
| `/t/<slug>/pr/journals/<pk>/` | Journal detail | Journal info with pay breakdown |
| `/t/<slug>/pr/journals/<pk>/calculate/` | Calculate journal | Calculate gross, taxes, deductions, net |
| `/t/<slug>/pr/journals/<pk>/approve/` | Approve journal | Approve a calculated journal |
| `/t/<slug>/pr/journals/<pk>/post/` | Post journal | Post to GL (creates journal entry) |
| **Payroll — Tax Management** | | |
| `/t/<slug>/pr/tax-withholdings/` | Withholding list | All tax withholdings |
| `/t/<slug>/pr/tax-withholdings/create/` | Create withholding | New tax withholding config |
| `/t/<slug>/pr/tax-withholdings/<pk>/edit/` | Edit withholding | Edit withholding rate/limit |
| `/t/<slug>/pr/remittances/` | Remittance list | All tax remittances |
| `/t/<slug>/pr/remittances/create/` | Create remittance | New tax remittance |
| `/t/<slug>/pr/remittances/<pk>/` | Remittance detail | Remittance info and payment status |
| `/t/<slug>/pr/remittances/<pk>/pay/` | Pay remittance | Mark remittance as paid (posts GL) |
| **Payroll — Benefits Accounting** | | |
| `/t/<slug>/pr/benefits/` | Benefit plan list | All benefit plans |
| `/t/<slug>/pr/benefits/create/` | Create plan | New benefit plan form |
| `/t/<slug>/pr/benefits/<pk>/` | Plan detail | Plan info with enrolled employees |
| `/t/<slug>/pr/benefits/<pk>/edit/` | Edit plan | Edit benefit plan |
| `/t/<slug>/pr/benefits/enroll/` | Enroll employee | Enroll employee in plan |
| `/t/<slug>/pr/benefits/enroll/<pk>/edit/` | Edit enrollment | Edit enrollment details |
| **Payroll — Garnishments** | | |
| `/t/<slug>/pr/garnishments/` | Garnishment list | All garnishments with filters |
| `/t/<slug>/pr/garnishments/create/` | Create garnishment | New garnishment order |
| `/t/<slug>/pr/garnishments/<pk>/` | Garnishment detail | Garnishment info with progress |
| `/t/<slug>/pr/garnishments/<pk>/edit/` | Edit garnishment | Edit garnishment details |
| **Payroll — Workers Comp** | | |
| `/t/<slug>/pr/workers-comp/` | Comp class list | All workers comp classes |
| `/t/<slug>/pr/workers-comp/create/` | Create class | New workers comp class |
| `/t/<slug>/pr/workers-comp/<pk>/` | Class detail | Class info with assigned employees |
| `/t/<slug>/pr/workers-comp/<pk>/edit/` | Edit class | Edit workers comp class |
| `/t/<slug>/pr/workers-comp/assign/` | Assign employee | Assign employee to comp class |
| `/t/<slug>/pr/workers-comp/assign/<pk>/edit/` | Edit assignment | Edit comp assignment |
| **Payroll — Reconciliation** | | |
| `/t/<slug>/pr/reconciliation/` | Reconciliation list | All payroll reconciliations |
| `/t/<slug>/pr/reconciliation/create/` | Create reconciliation | Run gross-to-net reconciliation |
| `/t/<slug>/pr/reconciliation/<pk>/` | Reconciliation detail | Reconciliation breakdown with variance |
| **Project/Job Costing — Projects** | | |
| `/t/<slug>/pj/projects/` | Project list | All projects with filters |
| `/t/<slug>/pj/projects/create/` | Create project | New project form |
| `/t/<slug>/pj/projects/<pk>/` | Project detail | Project overview with WBS, budgets, milestones |
| `/t/<slug>/pj/projects/<pk>/edit/` | Edit project | Edit project details |
| **Project/Job Costing — WBS Elements** | | |
| `/t/<slug>/pj/projects/<project_pk>/wbs/` | WBS list | WBS elements for a project |
| `/t/<slug>/pj/projects/<project_pk>/wbs/create/` | Create WBS | New WBS element form |
| `/t/<slug>/pj/projects/<project_pk>/wbs/<pk>/edit/` | Edit WBS | Edit WBS element |
| `/t/<slug>/pj/projects/<project_pk>/wbs/<pk>/delete/` | Delete WBS | Delete WBS element |
| **Project/Job Costing — Budgets** | | |
| `/t/<slug>/pj/projects/<project_pk>/budgets/` | Budget list | Project budgets with GL accounts |
| `/t/<slug>/pj/projects/<project_pk>/budgets/create/` | Create budget | New budget line item |
| `/t/<slug>/pj/projects/<project_pk>/budgets/<pk>/edit/` | Edit budget | Edit budget line |
| `/t/<slug>/pj/projects/<project_pk>/budgets/<pk>/delete/` | Delete budget | Delete budget line |
| **Project/Job Costing — Billing Rules** | | |
| `/t/<slug>/pj/projects/<project_pk>/billing-rules/` | Billing rule list | Billing rules for a project |
| `/t/<slug>/pj/projects/<project_pk>/billing-rules/create/` | Create rule | New billing rule form |
| `/t/<slug>/pj/projects/<project_pk>/billing-rules/<pk>/edit/` | Edit rule | Edit billing rule |
| `/t/<slug>/pj/projects/<project_pk>/billing-rules/<pk>/delete/` | Delete rule | Delete billing rule |
| **Project/Job Costing — Time Entries** | | |
| `/t/<slug>/pj/time-entries/` | Time entry list | All time entries with filters |
| `/t/<slug>/pj/time-entries/create/` | Create time entry | New time entry form |
| `/t/<slug>/pj/time-entries/<pk>/edit/` | Edit time entry | Edit time entry |
| `/t/<slug>/pj/time-entries/<pk>/delete/` | Delete time entry | Delete time entry |
| `/t/<slug>/pj/time-entries/<pk>/approve/` | Approve time entry | Approve a time entry |
| **Project/Job Costing — Expenses** | | |
| `/t/<slug>/pj/expenses/` | Expense list | All expenses with filters |
| `/t/<slug>/pj/expenses/create/` | Create expense | New expense entry form |
| `/t/<slug>/pj/expenses/<pk>/edit/` | Edit expense | Edit expense entry |
| `/t/<slug>/pj/expenses/<pk>/delete/` | Delete expense | Delete expense entry |
| **Project/Job Costing — Revenue Recognition** | | |
| `/t/<slug>/pj/revenue-recognition/` | Revenue recognition list | All revenue recognition records |
| `/t/<slug>/pj/revenue-recognition/create/` | Create recognition | New revenue recognition entry |
| `/t/<slug>/pj/revenue-recognition/<pk>/` | Recognition detail | Revenue recognition detail with GL link |
| `/t/<slug>/pj/revenue-recognition/<pk>/calculate/` | Calculate | Recalculate revenue recognition |
| `/t/<slug>/pj/revenue-recognition/<pk>/post/` | Post recognition | Post revenue recognition |
| **Project/Job Costing — Milestones** | | |
| `/t/<slug>/pj/projects/<project_pk>/milestones/` | Milestone list | Project milestones with amounts |
| `/t/<slug>/pj/projects/<project_pk>/milestones/create/` | Create milestone | New milestone form |
| `/t/<slug>/pj/projects/<project_pk>/milestones/<pk>/edit/` | Edit milestone | Edit milestone details |
| `/t/<slug>/pj/projects/<project_pk>/milestones/<pk>/complete/` | Complete milestone | Mark milestone as completed |
| **Project/Job Costing — Invoices** | | |
| `/t/<slug>/pj/invoices/` | Invoice list | All project invoices with filters |
| `/t/<slug>/pj/invoices/create/` | Create invoice | New project invoice with line items |
| `/t/<slug>/pj/invoices/<pk>/` | Invoice detail | Invoice info with lines and WBS |
| `/t/<slug>/pj/invoices/<pk>/approve/` | Approve invoice | Approve a project invoice |
| `/t/<slug>/pj/invoices/<pk>/void/` | Void invoice | Void a project invoice |
| **Project/Job Costing — Profitability** | | |
| `/t/<slug>/pj/profitability/` | Profitability dashboard | Project profitability overview |
| `/t/<slug>/pj/profitability/snapshots/` | Snapshot list | All profitability snapshots |
| `/t/<slug>/pj/profitability/<project_pk>/` | Profitability detail | Detailed project profitability analysis |
| `/t/<slug>/pj/profitability/<project_pk>/snapshot/` | Create snapshot | Take profitability snapshot |
| **Project/Job Costing — Resource Planning** | | |
| `/t/<slug>/pj/resources/` | Assignment list | All resource assignments |
| `/t/<slug>/pj/resources/create/` | Create assignment | New resource assignment form |
| `/t/<slug>/pj/resources/<pk>/edit/` | Edit assignment | Edit resource assignment |
| `/t/<slug>/pj/resources/<pk>/delete/` | Delete assignment | Delete resource assignment |
| `/t/<slug>/pj/resources/utilization/` | Utilization report | Employee utilization report |
| **Multi-Entity — Entities** | | |
| `/t/<slug>/me/entities/` | Entity list | All entities with filters |
| `/t/<slug>/me/entities/create/` | Create entity | New entity form |
| `/t/<slug>/me/entities/<pk>/` | Entity detail | Entity info, hierarchy, IC accounts |
| `/t/<slug>/me/entities/<pk>/edit/` | Edit entity | Edit entity details |
| `/t/<slug>/me/entities/hierarchy/` | Entity hierarchy | Tree view of entity structure |
| **Multi-Entity — Intercompany** | | |
| `/t/<slug>/me/ic-transactions/` | IC transaction list | All intercompany transactions |
| `/t/<slug>/me/ic-transactions/create/` | Create IC transaction | New intercompany transaction |
| `/t/<slug>/me/ic-transactions/<pk>/` | IC transaction detail | Transaction info, linked JEs |
| `/t/<slug>/me/ic-transactions/<pk>/confirm/` | Confirm IC transaction | Confirm a draft transaction |
| `/t/<slug>/me/ic-transactions/<pk>/post/` | Post IC transaction | Post confirmed transaction (creates paired JEs) |
| `/t/<slug>/me/ic-balances/` | IC balance list | Intercompany balances by entity pair |
| `/t/<slug>/me/ic-balances/<pk>/reconcile/` | Reconcile IC balance | Mark IC balance as reconciled |
| **Multi-Entity — Currency Translation** | | |
| `/t/<slug>/me/translation/rules/` | Translation rule list | Currency translation rules |
| `/t/<slug>/me/translation/rules/create/` | Create translation rule | New translation rule |
| `/t/<slug>/me/translation/rules/<pk>/edit/` | Edit translation rule | Edit translation rule |
| `/t/<slug>/me/translation/run/` | Run translation | Execute currency translation |
| `/t/<slug>/me/translation/adjustments/` | CTA adjustment list | Translation adjustments |
| `/t/<slug>/me/translation/adjustments/<pk>/` | CTA adjustment detail | View CTA detail |
| **Multi-Entity — Consolidation** | | |
| `/t/<slug>/me/consolidation/groups/` | Group list | Consolidation groups |
| `/t/<slug>/me/consolidation/groups/create/` | Create group | New consolidation group |
| `/t/<slug>/me/consolidation/groups/<pk>/` | Group detail | Group info, entities, rules |
| `/t/<slug>/me/consolidation/groups/<pk>/edit/` | Edit group | Edit consolidation group |
| `/t/<slug>/me/consolidation/rules/` | Elimination rule list | All elimination rules |
| `/t/<slug>/me/consolidation/rules/create/` | Create elimination rule | New elimination rule |
| `/t/<slug>/me/consolidation/rules/<pk>/edit/` | Edit elimination rule | Edit elimination rule |
| `/t/<slug>/me/consolidation/runs/` | Run list | All consolidation runs |
| `/t/<slug>/me/consolidation/runs/create/` | Create run | New consolidation run |
| `/t/<slug>/me/consolidation/runs/<pk>/` | Run detail | Run info, elimination entries, NCI |
| `/t/<slug>/me/consolidation/runs/<pk>/execute/` | Execute run | Execute consolidation run |
| `/t/<slug>/me/consolidation/runs/<pk>/reverse/` | Reverse run | Reverse completed run |
| **Multi-Entity — Transfer Pricing** | | |
| `/t/<slug>/me/transfer-pricing/policies/` | TP policy list | Transfer pricing policies |
| `/t/<slug>/me/transfer-pricing/policies/create/` | Create TP policy | New transfer pricing policy |
| `/t/<slug>/me/transfer-pricing/policies/<pk>/` | TP policy detail | Policy info, transactions |
| `/t/<slug>/me/transfer-pricing/policies/<pk>/edit/` | Edit TP policy | Edit transfer pricing policy |
| `/t/<slug>/me/transfer-pricing/transactions/` | TP transaction list | TP transactions with variance |
| `/t/<slug>/me/transfer-pricing/transactions/create/` | Create TP transaction | New TP transaction |
| `/t/<slug>/me/transfer-pricing/transactions/<pk>/review/` | Review TP transaction | Approve or flag TP transaction |
| **Multi-Entity — Regulatory** | | |
| `/t/<slug>/me/regulatory/adjustments/` | GAAP adjustment list | Local GAAP adjustments |
| `/t/<slug>/me/regulatory/adjustments/create/` | Create GAAP adjustment | New GAAP adjustment |
| `/t/<slug>/me/regulatory/adjustments/<pk>/` | GAAP adjustment detail | Adjustment info, JE |
| `/t/<slug>/me/regulatory/adjustments/<pk>/post/` | Post GAAP adjustment | Post adjustment (creates JE) |
| `/t/<slug>/me/regulatory/reports/` | Report list | Regulatory reports |
| `/t/<slug>/me/regulatory/reports/create/` | Create report | New regulatory report |
| `/t/<slug>/me/regulatory/reports/<pk>/` | Report detail | Report info, data |
| `/t/<slug>/me/regulatory/reports/<pk>/file/` | File report | Mark report as filed |
| **Tax — Sales Tax Engine (Jurisdictions)** | | |
| `/t/<slug>/tx/jurisdictions/` | Jurisdiction list | All tax jurisdictions with filters |
| `/t/<slug>/tx/jurisdictions/create/` | Create jurisdiction | New jurisdiction form |
| `/t/<slug>/tx/jurisdictions/<pk>/` | Jurisdiction detail | Jurisdiction info, child jurisdictions, rates, rules |
| `/t/<slug>/tx/jurisdictions/<pk>/edit/` | Edit jurisdiction | Edit jurisdiction details |
| **Tax — Sales Tax Engine (Rates, Rules, Groups)** | | |
| `/t/<slug>/tx/tax-rates/` | Tax rate list | All tax rates with jurisdiction filter |
| `/t/<slug>/tx/tax-rates/create/` | Create tax rate | New tax rate with GL accounts |
| `/t/<slug>/tx/tax-rates/<pk>/edit/` | Edit tax rate | Edit tax rate details |
| `/t/<slug>/tx/tax-rules/` | Tax rule list | All taxability rules with type filter |
| `/t/<slug>/tx/tax-rules/create/` | Create tax rule | New taxability rule |
| `/t/<slug>/tx/tax-rules/<pk>/edit/` | Edit tax rule | Edit taxability rule |
| `/t/<slug>/tx/tax-groups/` | Tax group list | All tax groups with combined rates |
| `/t/<slug>/tx/tax-groups/create/` | Create tax group | New tax group with member rates |
| `/t/<slug>/tx/tax-groups/<pk>/` | Tax group detail | Group info, member rates, combined rate |
| `/t/<slug>/tx/tax-groups/<pk>/edit/` | Edit tax group | Edit group and member rates |
| **Tax — Tax Returns** | | |
| `/t/<slug>/tx/returns/` | Return list | All tax returns with status filters |
| `/t/<slug>/tx/returns/create/` | Create return | New tax return with line items |
| `/t/<slug>/tx/returns/<pk>/` | Return detail | Return info, lines, payments, workflow actions |
| `/t/<slug>/tx/returns/<pk>/edit/` | Edit return | Edit draft/calculated return |
| `/t/<slug>/tx/returns/<pk>/calculate/` | Calculate return | Compute return totals from lines |
| `/t/<slug>/tx/returns/<pk>/file/` | File return | Mark return as filed |
| `/t/<slug>/tx/returns/<pk>/payment/` | Record payment | Add payment to return (posts GL) |
| **Tax — Use Tax Tracking** | | |
| `/t/<slug>/tx/use-tax/` | Assessment list | All use tax assessments with status filter |
| `/t/<slug>/tx/use-tax/create/` | Create assessment | New use tax assessment linked to vendor |
| `/t/<slug>/tx/use-tax/<pk>/` | Assessment detail | Assessment info, vendor, GL links |
| `/t/<slug>/tx/use-tax/<pk>/accrue/` | Accrue assessment | Post use tax accrual to GL |
| `/t/<slug>/tx/use-tax/accruals/` | Accrual list | All use tax accruals |
| `/t/<slug>/tx/use-tax/accruals/create/` | Create accrual | New period accrual |
| `/t/<slug>/tx/use-tax/accruals/<pk>/` | Accrual detail | Accrual info, totals, GL link |
| `/t/<slug>/tx/use-tax/accruals/<pk>/post/` | Post accrual | Post accrual to GL |
| **Tax — Income Tax Provision** | | |
| `/t/<slug>/tx/provisions/` | Provision list | All provisions with ETR display |
| `/t/<slug>/tx/provisions/create/` | Create provision | New income tax provision |
| `/t/<slug>/tx/provisions/<pk>/` | Provision detail | Tax computation, deferred items, ETR reconciliation |
| `/t/<slug>/tx/provisions/<pk>/edit/` | Edit provision | Edit with deferred items & ETR formsets |
| `/t/<slug>/tx/provisions/<pk>/calculate/` | Calculate provision | Compute current/deferred tax and ETR |
| `/t/<slug>/tx/provisions/<pk>/post/` | Post provision | Post provision to GL |
| **Tax — Tax Calendar** | | |
| `/t/<slug>/tx/calendar/` | Deadline list | All deadlines with overdue alerts |
| `/t/<slug>/tx/calendar/create/` | Create deadline | New tax filing deadline |
| `/t/<slug>/tx/calendar/<pk>/` | Deadline detail | Deadline info, reminders |
| `/t/<slug>/tx/calendar/<pk>/edit/` | Edit deadline | Edit deadline details |
| `/t/<slug>/tx/calendar/<pk>/complete/` | Complete deadline | Mark deadline as filed |
| `/t/<slug>/tx/calendar/generate/` | Generate recurring | Generate recurring deadlines for date range |
| **Tax — Audit Support** | | |
| `/t/<slug>/tx/audits/` | Audit list | All tax audits with status filters |
| `/t/<slug>/tx/audits/create/` | Create audit | New tax audit record |
| `/t/<slug>/tx/audits/<pk>/` | Audit detail | Audit info, findings, documents |
| `/t/<slug>/tx/audits/<pk>/edit/` | Edit audit | Edit audit details |
| `/t/<slug>/tx/audits/<pk>/findings/create/` | Add finding | New audit finding |
| `/t/<slug>/tx/audits/<pk>/findings/<finding_pk>/edit/` | Edit finding | Edit audit finding |
| `/t/<slug>/tx/audits/<pk>/documents/upload/` | Upload document | Upload audit document |
| **Tax — Nexus Tracking** | | |
| `/t/<slug>/tx/nexus/` | Nexus list | All nexus jurisdictions with threshold progress |
| `/t/<slug>/tx/nexus/create/` | Create nexus | New nexus jurisdiction tracking |
| `/t/<slug>/tx/nexus/dashboard/` | Nexus dashboard | Threshold alerts and overview |
| `/t/<slug>/tx/nexus/<pk>/` | Nexus detail | Nexus info, activity history, threshold progress |
| `/t/<slug>/tx/nexus/<pk>/edit/` | Edit nexus | Edit nexus jurisdiction details |
| `/t/<slug>/tx/nexus/<pk>/activity/create/` | Add activity | Record nexus activity period |

---

## Django Apps

### 1. `core` — Abstract Models & Utilities
- `TimeStampedModel` — Adds `created_at`, `updated_at` to all models
- `TenantAwareModel` — Abstract base with automatic tenant assignment on save
- Template tags: `kpi_card`, `currency`, `percentage` filters

### 2. `tenants` — Multi-Tenant Engine
- **Tenant** — Organization with name, slug, domain, logo, owner
- **TenantMembership** — Links users to tenants with default flag
- **TenantMiddleware** — Resolves tenant from URL/session/user default
- **TenantAwareManager** — Auto-filters queries by current tenant
- Context processor injects `current_tenant` and `user_tenants` into templates

### 3. `accounts` — Authentication & Users
- **CustomUser** — Extends `AbstractUser`, email as `USERNAME_FIELD`, avatar, phone
- **UserProfile** — Per-tenant profile (job title, department, timezone, bio)
- **UserInvitation** — Token-based invitation with role assignment and expiration
- Custom allauth adapter for auto-tenant creation on signup

### 4. `roles` — Permissions & RBAC
- **Permission** — System-wide permission definitions (codename, name, module)
- **Role** — Tenant-scoped role with M2M permissions, supports system roles
- **TenantUserRole** — Assigns roles to users within a specific tenant
- Decorators: `@tenant_required`, `@role_required(*role_names)`

### 5. `company` — Company Configuration
- **Currency** — ISO 4217 currencies (code, name, symbol, decimal places)
- **CompanySettings** — One per tenant (company name, address, tax ID, base currency)
- **FiscalYear** — Start/end dates, is_current, is_closed flags
- **FiscalPeriod** — Monthly periods within a fiscal year
- **AccountType** — 5 standard types (Asset, Liability, Equity, Revenue, Expense)
- **ChartOfAccountsTemplate** — Pre-built COA with hierarchical accounts

### 6. `general_ledger` — General Ledger Module

The backbone of double-entry accounting with 8 submodules, 10 models, 28 views, and 18 templates.

- **Account** — Tenant-scoped chart of accounts with hierarchical parent-child structure, imported from COA templates
- **JournalEntry** — Double-entry journal entries with status workflow (Draft → Pending → Approved → Posted), auto-generated entry numbers (`JE-YYYY-NNNN`)
- **JournalEntryLine** — Debit/credit lines linked to GL accounts, with multi-currency support
- **JournalApproval** — Multi-level approval workflow with comments and approval history
- **PeriodCloseChecklist** — Month-end/year-end closing procedures with step-by-step checklists and progress tracking
- **AccountReconciliation** — Account balance verification with expected vs actual balance comparison, auto-difference calculation
- **AllocationRule** / **AllocationRuleLine** — Automatic cost distribution rules with percentage/fixed-amount targets, generates journal entries on execution
- **AuditTrail** — Immutable log of all GL changes via Django signals (pre_save/post_save), tracks field-level old/new values
- **ExchangeRate** — Multi-currency exchange rate management with effective dates and source tracking

#### Journal Entry Workflow

```
Draft → Submit for Approval → Pending Approval → Approve → Approved → Post → Posted
                                                → Reject → Rejected
```

### 7. `accounts_payable` — Accounts Payable Module

Full accounts payable lifecycle with 8 submodules, 13 models, 38 views, 6 portal views, and 29 templates.

- **PaymentTerm** — Configurable payment terms (e.g., Net 30, 2/10 Net 30) with discount percentages and days
- **Vendor** — Vendor profiles with auto-generated numbers (`VND-NNNN`), tax ID, 1099/W-9 tracking, bank info, preferred payment method, default expense account
- **VendorContact** — Multiple contacts per vendor with primary flag
- **Bill** — Vendor invoices with status workflow (Draft → Pending Approval → Approved → Partially Paid → Paid → Void), auto-generated numbers (`BILL-YYYY-NNNN`), line items linked to GL accounts
- **BillLine** — Individual line items with account, quantity, unit price, auto-calculated amounts
- **BillApproval** — Bill approval workflow with approver, status, and comments
- **BillUpload** — Invoice document uploads with OCR status tracking and extracted data (JSONField), ready for future AI/OCR integration
- **Payment** — Payments with multiple methods (check, ACH, wire, virtual card), auto-generated numbers (`PAY-YYYY-NNNN`), GL journal entry creation via services
- **PaymentAllocation** — Links payments to bills with amount and discount tracking
- **PaymentBatch** — Batch payment processing with auto-generated numbers (`BATCH-YYYY-NNNN`)
- **ScheduledPayment** — Cash flow-optimized payment scheduling with priority levels
- **VendorPortalToken** — Token-based vendor portal authentication (no Django user required), with expiration
- **VendorMessage** — Two-way messaging between vendors and internal staff

#### Bill Workflow

```
Draft → Submit for Approval → Pending Approval → Approve → Approved → Pay → Partially Paid / Paid
                                                → Reject → Rejected
                                                                    → Void
```

#### Payment Workflow

```
Draft → Submit → Pending → Complete → Completed
                                   → Void
```

#### GL Integration

When a payment is completed, `services.py` creates a posted journal entry:
- **Debit**: Accounts Payable (2110)
- **Credit**: Bank/Checking Account (1110)
- **Credit**: Purchase Discounts (if early payment discount taken)

#### Vendor Portal

A standalone portal outside the tenant-scoped URLs (`/vendor-portal/...`) that uses token-based authentication:
- Vendors access via a unique 64-character token (no Django user account needed)
- Dashboard shows outstanding bills, recent payments, and unread messages
- Read-only bill detail view
- Two-way messaging system
- Session-based with automatic expiration

### 8. `accounts_receivable` — Accounts Receivable Module

Full accounts receivable lifecycle with 9 submodules, 14 models, 43 views, 9 portal views, and 31 templates.

- **Customer** — Customer profiles with auto-generated numbers (`CUST-NNNN`), tax ID, credit limits, credit hold management, billing & shipping addresses, preferred payment method, default revenue account
- **CustomerContact** — Multiple contacts per customer with primary and billing contact flags
- **Invoice** — Customer invoices with status workflow (Draft → Submitted → Approved → Sent → Partially Paid → Paid → Void/Written Off), auto-generated numbers (`INV-YYYY-NNNN`), line items linked to GL revenue accounts
- **InvoiceLine** — Individual line items with account, quantity, unit price, auto-calculated amounts
- **InvoiceApproval** — Invoice approval workflow with approver, status, and comments
- **Receipt** — Incoming payments with multiple methods (check, ACH, wire, credit card, cash, online), auto-generated numbers (`RCT-YYYY-NNNN`), GL journal entry creation via services
- **ReceiptAllocation** — Links receipts to invoices with amount and discount tracking
- **RecurringInvoiceTemplate** — Automated invoice generation on configurable schedules (weekly/biweekly/monthly/quarterly/semiannual/annual), auto-generated numbers (`REC-YYYY-NNNN`)
- **RecurringInvoiceTemplateLine** — Line items for recurring templates
- **CreditMemo** — Credit adjustments with approval workflow, auto-generated numbers (`CM-YYYY-NNNN`), optional link to original invoice
- **CollectionActivity** — Dunning workflow with 4 escalation levels (Reminder → Past Due → Urgent → Final Notice), activity types include phone calls, emails, letters, promise-to-pay tracking
- **WriteOff** — Bad debt write-offs with approval workflow, GL journal entry for bad debt expense
- **CustomerPortalToken** — Token-based customer portal authentication (no Django user required), with expiration
- **CustomerMessage** — Two-way messaging between customers and internal staff

#### Invoice Workflow

```
Draft → Submit for Approval → Submitted → Approve → Approved → Send → Sent → Pay → Partially Paid / Paid
                                         → Reject → Rejected
                                                                                  → Void
                                                                                  → Write Off
```

#### Receipt Workflow

```
Draft → Submit → Pending → Complete → Completed
                                   → Void
```

#### GL Integration

When a receipt is completed, `services.py` creates a posted journal entry:
- **Debit**: Bank/Cash Account (1110)
- **Credit**: Accounts Receivable (1210)
- **Debit**: Sales Discount (if early payment discount given)

When a credit memo is approved:
- **Debit**: Sales Returns/AR Control
- **Credit**: Accounts Receivable (1210)

When a write-off is approved:
- **Debit**: Bad Debt Expense
- **Credit**: Accounts Receivable (1210)

#### Cash Application

Auto-match engine uses FIFO logic to allocate unmatched receipts to open invoices, matching by customer and applying payments to the oldest invoices first.

#### Collections & Dunning

- 4-level dunning escalation (Reminder → Past Due → Urgent → Final Notice)
- Activity tracking: phone calls, emails, dunning letters, meetings, promise-to-pay
- Follow-up date tracking and resolution flags
- Dashboard showing overdue invoices grouped by aging bucket

#### Customer Portal

A standalone portal outside the tenant-scoped URLs (`/customer-portal/...`) that uses token-based authentication:
- Customers access via a unique 64-character token (no Django user account needed)
- Dashboard shows outstanding invoices, recent payments, and unread messages
- Invoice list with filtering and invoice detail views
- Payment submission interface
- Two-way messaging system
- Session-based with automatic expiration

### 9. `cash_management` — Cash Management Module

Full cash management lifecycle with 7 submodules, 11 models, 34 views, and 23 templates.

- **BankAccount** — Bank account profiles with auto-generated numbers (`BNK-NNNN`), linked to GL accounts, masked account numbers, support for checking/savings/money market/credit line, multi-currency, opening and current balance tracking
- **BankAccountSignatory** — Authorized signatories per bank account with signature level (primary/secondary) and authorization limits
- **BankFeed** — Bank feed connections with multiple source types (manual CSV, OFX, Plaid, Yodlee, Open Banking), status tracking, and connection configuration
- **BankTransaction** — Bank transactions with auto-generated numbers (`BTX-YYYY-NNNN`), debit/credit types, matching status, CSV import support with batch tracking and raw data storage
- **BankReconciliation** — Bank account reconciliation with statement balance vs GL balance comparison, auto-generated reconciliation periods, status workflow (In Progress → Completed → Reviewed)
- **ReconciliationItem** — Individual matched/unmatched items linking bank transactions to GL journal entry lines, with match type tracking (auto/manual/exception)
- **AutoMatchRule** — Configurable auto-match rules with priority ordering, supporting exact amount matching, reference matching, date range, and description pattern matching
- **CashForecast** — Cash flow forecasts with auto-generated numbers (`FCT-YYYY-NNNN`), short-term and long-term types, status workflow (Draft → Active → Archived)
- **CashForecastLine** — Individual forecast line items with categories (AR collections, AP payments, payroll, tax, loan, other), expected vs actual amounts, and variance tracking
- **IntercompanyTransfer** — Intercompany fund transfers with auto-generated numbers (`ICT-YYYY-NNNN`), multi-currency with exchange rates, approval workflow (Draft → Pending → Completed/Cancelled), automatic GL journal entry creation on completion
- **BankFee** — Bank fee tracking with fee types (monthly maintenance, transaction, wire, overdraft, ATM, foreign exchange, other), recurring flag, and category classification

#### Bank Reconciliation Workflow

```
In Progress → Auto-Match / Manual Match → Complete → Completed → Review → Reviewed
```

#### Intercompany Transfer Workflow

```
Draft → Submit → Pending → Approve → Completed (creates GL Journal Entry)
                         → Cancel → Cancelled
```

#### GL Integration

When an intercompany transfer is completed, `services.py` creates a posted journal entry:
- **Debit**: Destination bank account's GL account (increase)
- **Credit**: Source bank account's GL account (decrease)

#### Auto-Match Engine

The reconciliation engine supports configurable matching rules executed by priority:
- **Exact Amount** — Matches bank debits to GL credits (and vice versa) by exact amount
- **Reference Match** — Matches by transaction reference/check number to GL entry reference

#### Cash Position Dashboard

Aggregates all active bank account balances with real-time inflows/outflows for a given date, providing a consolidated treasury view.

#### CSV Transaction Import

Parses uploaded CSV files with flexible column detection (Date, Description, Amount, Debit/Credit), supports multiple date formats, and creates batch-tracked `BankTransaction` records.

### 10. `fixed_assets` — Fixed Assets Module

Full fixed asset lifecycle management with 8 submodules, 14 models, 30+ views, and 20 templates.

- **AssetCategory** — Asset classification with GL account mapping (asset, depreciation expense, accumulated depreciation accounts), default useful life and salvage percentage, depreciation method defaults
- **AssetLocation** — Physical locations with code/name/address tracking
- **Asset** — Master asset records with auto-generated numbers (`AST-YYYY-NNNN`), status workflow (In Service, Under Maintenance, Disposed, Written Off, CIP), serial/barcode/tag tracking, custodian assignment, warranty and manufacturer info
- **AssetAcquisition** — Acquisition tracking with auto-generated numbers (`ACQ-YYYY-NNNN`), types (purchase/lease/donation/construction/transfer-in), vendor and invoice references, capitalization with GL journal entry creation
- **DepreciationProfile** — One-to-one with Asset, configurable method (straight-line/declining balance/units of production), useful life, salvage value, declining balance rate, total units for UoP
- **DepreciationSchedule** — Pre-computed monthly depreciation schedule lines with period amounts, accumulated depreciation, and net book value
- **DepreciationEntry** — Batch depreciation run header with auto-generated numbers (`DEP-YYYY-NNNN`), status workflow (Draft → Posted), GL journal entry creation
- **AssetTransfer** — Location/department/custodian transfers with auto-generated numbers (`ATR-YYYY-NNNN`), approval workflow (Draft → Pending → Completed/Cancelled)
- **AssetDisposal** — Asset disposal with auto-generated numbers (`DSP-YYYY-NNNN`), types (sale/scrap/write-off/donation/trade-in), automatic gain/loss calculation, GL journal entry creation
- **ImpairmentTest** — Impairment testing with automatic recoverable amount calculation (max of value-in-use and fair value less costs), impairment loss determination, GL journal entry creation
- **PhysicalInventory** — Physical inventory counts with auto-generated numbers (`INV-YYYY-NNNN`), status workflow (Planned → In Progress → Completed → Reconciled), auto-population of items from assets at selected location
- **PhysicalInventoryItem** — Individual count items with expected/found location, barcode scanning, condition tracking (Good/Fair/Poor/Damaged)
- **TaxDepreciationBook** — Parallel tax depreciation books supporting MACRS, bonus depreciation, Section 179, and custom methods
- **TaxDepreciationEntry** — Per-asset per-year tax depreciation records with recovery period, convention (half-year/mid-quarter/mid-month), and property class

#### Depreciation Methods

| Method | Description |
|--------|-------------|
| Straight-Line | Equal depreciation over useful life, prorated for partial periods |
| Declining Balance | Accelerated depreciation using configurable rate (e.g., 200% for DDB) |
| Units of Production | Depreciation based on actual usage vs total estimated units |

#### Asset Transfer Workflow

```
Draft → Submit → Pending → Approve → Completed
                          → Cancel → Cancelled
```

#### Asset Disposal Workflow

```
Draft → Submit → Pending → Process → Completed (creates GL Journal Entry with gain/loss)
                          → Cancel → Cancelled
```

#### GL Integration

When an acquisition is capitalized, `services.py` creates a posted journal entry:
- **Debit**: Asset GL account (from category)
- **Credit**: Accounts Payable / Cash account

When depreciation is run, `services.py` creates a posted journal entry:
- **Debit**: Depreciation Expense account (from category)
- **Credit**: Accumulated Depreciation account (from category)

When a disposal is processed:
- **Debit**: Accumulated Depreciation, Cash/Proceeds (if sale)
- **Credit**: Asset account
- **Debit/Credit**: Gain or Loss on Disposal (computed automatically)

When impairment is recorded:
- **Debit**: Impairment Loss
- **Credit**: Accumulated Depreciation (asset write-down)

### 11. `inventory` — Inventory & Cost Management Module

Full inventory and cost management lifecycle with 8 submodules, 22 models, 55 views, and 39 templates.

- **ItemCategory** — Hierarchical item classification with parent-child structure, auto-generated codes
- **UnitOfMeasure** — Units of measure with code, name, and abbreviation (e.g., EA, KG, LTR)
- **Item** — Master item records with auto-generated SKUs (`ITM-NNNN`), types (inventory/non-inventory/service), costing methods (FIFO/LIFO/weighted average/standard), quantity tracking, reorder points, safety stock levels, preferred vendor
- **CostLayer** — FIFO/LIFO cost layers with receipt date, original/remaining quantity, unit cost, source tracking (receipt/adjustment/opening balance), depletion status
- **Warehouse** — Storage locations with code/name/address tracking
- **PurchaseRequisition** — Internal purchase requests with auto-generated numbers (`REQ-YYYY-NNNN`), status workflow (Draft → Submitted → Approved → Converted → Rejected), line items with item/quantity/estimated cost
- **PurchaseRequisitionLine** — Individual requisition line items
- **PurchaseOrder** — Vendor purchase orders with auto-generated numbers (`PO-YYYY-NNNN`), status workflow (Draft → Approved → Partially Received → Received → Cancelled), vendor reference, line items with pricing
- **PurchaseOrderLine** — Individual PO line items with received quantity tracking
- **GoodsReceipt** — Goods receipt against POs with auto-generated numbers (`GRN-YYYY-NNNN`), status workflow (Draft → Posted → Cancelled), warehouse assignment, GL journal entry creation
- **GoodsReceiptLine** — Individual receipt lines with accepted/rejected quantities
- **InventoryTransaction** — All inventory movements with auto-generated numbers (`TXN-YYYY-NNNN`), types (receipt/issue/adjustment/scrap/transfer_in/transfer_out), quantity, cost, warehouse, GL journal entry for adjustments
- **InventoryTransfer** — Inter-warehouse transfers with auto-generated numbers (`TRF-YYYY-NNNN`), status workflow (Draft → In Transit → Completed → Cancelled), line items
- **InventoryTransferLine** — Individual transfer line items with item/quantity
- **COGSCalculation** — COGS calculation runs with auto-generated numbers (`COGS-YYYY-NNNN`), methods (FIFO/LIFO/weighted average/standard), period-based, status workflow (Draft → Posted), GL journal entry creation
- **COGSEntry** — Individual COGS entries per item with quantity sold, unit cost, total cost
- **ReorderSuggestion** — Auto-generated reorder suggestions with current stock, reorder point, economic order quantity, suggested vendor, status workflow (Pending → Approved → Ordered → Dismissed)
- **CycleCountPlan** — Recurring count plans with frequency (daily/weekly/monthly/quarterly), item selection methods (ABC/random/category/all), next count date tracking
- **CycleCountSession** — Individual count sessions with auto-generated numbers (`CC-YYYY-NNNN`), status workflow (Open → In Progress → Completed → Approved), variance tracking
- **CycleCountItem** — Per-item count results with system quantity, counted quantity, variance, and variance value
- **LandedCostVoucher** — Landed cost allocation vouchers with auto-generated numbers (`LCV-YYYY-NNNN`), linked to goods receipt, status workflow (Draft → Posted → Cancelled), GL journal entry creation
- **LandedCostLine** — Individual cost lines with cost types (freight/insurance/customs/handling/other), vendor, amount
- **LandedCostAllocation** — Cost allocation to receipt items by value proportion

#### Costing Methods

| Method | Description |
|--------|-------------|
| FIFO | First In, First Out — oldest cost layers consumed first |
| LIFO | Last In, First Out — newest cost layers consumed first |
| Weighted Average | Running weighted average cost recalculated on each receipt |
| Standard | Fixed standard cost per item, variances tracked separately |

#### Purchase Order Workflow

```
Draft → Approve → Approved → Receive → Partially Received / Received
                                     → Cancel → Cancelled
```

#### Goods Receipt Workflow

```
Draft → Post → Posted (creates cost layers, updates item qty, GL Journal Entry)
             → Cancel → Cancelled
```

#### COGS Calculation Workflow

```
Draft → Post → Posted (creates GL Journal Entry)
```

#### GL Integration

When a goods receipt is posted, `services.py` creates a posted journal entry:
- **Debit**: Inventory Asset account
- **Credit**: Goods Received Not Invoiced / offset account

When an inventory adjustment is processed:
- **Debit/Credit**: Inventory Asset (increase/decrease)
- **Credit/Debit**: Adjustment Expense account

When COGS is posted:
- **Debit**: Cost of Goods Sold account
- **Credit**: Inventory Asset account

When a landed cost voucher is posted:
- **Debit**: Inventory Asset account (cost allocated to items)
- **Credit**: Accounts Payable / Expense account

When cycle count variances are approved:
- **Debit/Credit**: Inventory Asset (variance adjustment)
- **Credit/Debit**: Inventory Variance account

#### Reorder Planning

Auto-scan engine checks all items where `quantity_on_hand` falls below `reorder_point`, generates suggestions with economic order quantity, and supports one-click PO creation from approved suggestions.

### 12. `payroll` — Payroll Integration Module

Full payroll lifecycle with 7 submodules, 11 models, 36 views, and 22 templates.

- **Employee** — Employee profiles with auto-generated numbers (`EMP-NNNN`), pay types (salary/hourly), pay frequencies (weekly/biweekly/semimonthly/monthly), filing status, federal/state allowances, GL expense account mapping
- **PayrollJournal** — Payroll runs with auto-generated numbers (`PR-YYYY-NNNN`), status workflow (Draft → Calculated → Approved → Posted → Void), pay period tracking, fiscal period linkage, GL journal entry creation
- **PayrollJournalLine** — Individual employee pay details within a journal: gross pay, regular/overtime hours, tax withholdings (federal/state/local/SS/Medicare), benefits deductions, garnishment deductions, net pay
- **TaxWithholding** — Per-employee tax withholding configuration with 7 tax types (Federal, State, Local, Social Security, Medicare, FUTA, SUTA), rates, annual limits, YTD tracking, employer-paid flag
- **TaxRemittance** — Tax remittance tracking with auto-generated numbers (`TR-YYYY-NNNN`), status workflow (Pending → Paid → Overdue), GL journal entry on payment
- **BenefitPlan** — Benefit plans with types (401k, health/dental/vision insurance, life, HSA, FSA), employer contribution types (fixed/percentage/match), match limits, GL expense and liability account mapping
- **EmployeeBenefit** — Employee enrollment in benefit plans with per-period contribution amounts
- **Garnishment** — Court-ordered deductions with 6 types (child support, tax levy, student loan, creditor, bankruptcy, other), fixed or percentage amounts, priority ordering, max percentage of disposable income, total required/paid tracking with remaining balance
- **WorkersCompClass** — Workers compensation classification codes with rates per $100 payroll, effective dates, GL expense account mapping
- **WorkersCompAssignment** — Assignment of employees to workers comp classes with effective date tracking
- **PayrollReconciliation** — Gross-to-net reconciliation with auto-generated numbers (`REC-YYYY-NNNN`), status (Draft → Reconciled → Exception), total breakdown (gross, taxes, benefits, garnishments, net), variance detection

#### Payroll Journal Workflow

```
Draft → Calculate → Calculated → Approve → Approved → Post → Posted (creates GL Journal Entry)
                                                             → Void
```

#### GL Integration

When a payroll journal is posted, `services.py` creates a posted journal entry:
- **Debit**: Salary/Wage Expense account (per employee)
- **Credit**: Net Pay payable, Tax Withholdings payable

When a tax remittance is paid:
- Creates GL journal entry for the remittance payment

#### Payroll Calculation Engine

The calculation service (`services.py`) handles:
- **Hourly employees**: Regular hours × rate + overtime hours × 1.5× rate
- **Salaried employees**: Annual rate ÷ pay frequency divisor (52/26/24/12)
- **Tax withholdings**: Applies configured rates for each tax type
- **Benefits deductions**: Sums active employee contributions
- **Garnishments**: Applies priority-ordered deductions with remaining balance checks
- **Net pay**: Gross - all deductions

#### Gross-to-Net Reconciliation

Verifies payroll accuracy by comparing journal totals against line-level sums, flagging any variance as an exception for investigation.

### 13. `project_costing` — Project/Job Costing Module

Full project costing lifecycle with 11 submodules, 12 models, 40 views, and 34 templates.

- **Project** — Project master records with auto-generated numbers (`PJ-NNNN`), status workflow (Planning → Active → On Hold → Completed → Cancelled), billing types (time & materials/fixed price/cost plus), contract and budget amounts, retention percentage, manager assignment, revenue and expense GL account mapping
- **WBSElement** — Hierarchical work breakdown structure with parent-child relationships, level tracking, budget hours and amounts, billable flag, display ordering
- **ProjectBudget** — Budget line items linked to WBS elements and GL accounts, with original budget hours/rate/amount and revised amounts, fiscal period association
- **BillingRule** — Configurable billing rules with rate types (hourly/daily/fixed/percentage), markup percentages, effective date ranges
- **TimeEntry** — Employee time tracking with project/WBS assignment, hours and hourly rate, auto-calculated total amount, billing status (Unbilled → Billed / Non-Billable), approval workflow with approver and date
- **ExpenseEntry** — Project expense tracking with GL account mapping, vendor reference, auto-calculated billed amount with configurable markup percentage, billing status workflow
- **RevenueRecognition** — Revenue recognition with 3 methods (percentage-of-completion/milestone/completed-contract), fiscal period linkage, automatic calculation of cumulative and period-specific recognized amounts, GL journal entry posting
- **ProjectMilestone** — Project milestones with amounts, target/actual dates, status workflow (Pending → Completed → Billed), completion percentage tracking
- **ProjectInvoice** — Project invoices with auto-generated numbers (`PJI-NNNN`), status workflow (Draft → Approved → Sent → Paid → Void), line items with WBS linkage, automatic retention calculation, subtotal/tax/total computation, GL journal entry posting
- **ProjectInvoiceLine** — Invoice line items with types (time/expense/milestone/other), quantity, unit price, auto-calculated amounts, WBS element association
- **ProfitabilitySnapshot** — Point-in-time profitability snapshots with earned value metrics: budget amount, actual cost/revenue, committed cost, estimate at completion (EAC), estimate to complete (ETC), earned value, cost variance (CV), schedule variance (SV), cost performance index (CPI), schedule performance index (SPI)
- **ResourceAssignment** — Employee resource assignments to projects/WBS elements with role, allocation percentage, date ranges, planned vs actual hours tracking

#### Revenue Recognition Methods

| Method | Description |
|--------|-------------|
| Percentage of Completion | Revenue recognized based on completion percentage applied to contract amount |
| Milestone | Revenue recognized upon milestone completion |
| Completed Contract | Revenue recognized only when project is fully completed |

#### Project Status Workflow

```
Planning → Active → On Hold → Completed
                  → Cancelled
```

#### Project Invoice Workflow

```
Draft → Approve → Approved → Send → Sent → Pay → Paid
                                              → Void
```

#### Revenue Recognition Workflow

```
Draft → Calculate → Post → Posted (creates GL Journal Entry)
```

#### GL Integration

Revenue recognition creates a posted journal entry:
- **Debit**: Accounts Receivable / Unbilled Revenue
- **Credit**: Project Revenue account

#### Profitability Analysis

The profitability dashboard provides earned value management (EVM) metrics:
- **Cost Variance (CV)** — Earned Value minus Actual Cost
- **Schedule Variance (SV)** — Earned Value minus Planned Value
- **Cost Performance Index (CPI)** — Earned Value ÷ Actual Cost (>1.0 = under budget)
- **Schedule Performance Index (SPI)** — Earned Value ÷ Planned Value (>1.0 = ahead of schedule)

#### Audit Trail

6 models are tracked via the general ledger audit trail system: Project, ProjectInvoice, RevenueRecognition, TimeEntry, ExpenseEntry, ProfitabilitySnapshot.

### 14. `multi_entity` — Multi-Entity & Consolidation Module

Full multi-entity management with 6 submodules, 14 models, 40 views, and 30 templates.

- **Entity** — Organizational entities with code/name, types (parent/subsidiary/branch/division/joint venture/associate), hierarchical parent-child structure, functional currency, ownership percentage, consolidation method (full/proportional/equity/none), IC account mapping, status workflow (Active → Inactive → Dissolved)
- **IntercompanyTransaction** — IC transactions with auto-generated numbers (`ICX-YYYY-NNNN`), types (sale/purchase/service/loan/dividend/capital/expense allocation), paired journal entry creation (one per entity side), status workflow (Draft → Pending → Confirmed → Posted → Cancelled)
- **IntercompanyBalance** — Running due-to/due-from balances between entity pairs per fiscal period, reconciliation tracking
- **CurrencyTranslationRule** — Configurable translation rules by account type or specific account, rate types (current/historical/average/fixed)
- **TranslationAdjustment** — CTA entries per entity per period with translated amounts (assets/liabilities/equity/income/expense), cumulative CTA tracking
- **ConsolidationGroup** — Groups of entities for consolidation with M2M entity relationships, reporting currency, parent entity designation
- **ConsolidationRun** — Consolidation execution tracking with auto-generated numbers (`CON-YYYY-NNNN`), status workflow (Draft → In Progress → Completed → Failed → Reversed), elimination and NCI totals
- **EliminationRule** — Configurable elimination rules with types (IC receivable/payable, IC revenue/expense, investment/equity, dividend, inventory profit, custom), priority ordering, auto-apply flag
- **EliminationEntry** — Generated elimination journal entries from consolidation runs, linked to rules and entity pairs
- **MinorityInterest** — Non-controlling interest per entity per period with NCI percentage, income share, and equity share calculations
- **TransferPricingPolicy** — TP policies with auto-generated numbers (`TPP-YYYY-NNNN`), pricing methods (CUP/resale price/cost plus/TNMM/profit split), markup percentage, effective date ranges, documentation
- **TransferPricingTransaction** — TP analysis per IC transaction with transfer price vs arm's length price, variance calculation, status workflow (Draft → Reviewed → Approved → Flagged)
- **LocalGAAPAdjustment** — GAAP adjustments with auto-generated numbers (`GAP-YYYY-NNNN`), types (reclassification/measurement/disclosure/recognition), from/to accounting standards, GL journal entry creation on posting
- **RegulatoryReport** — Regulatory filings with auto-generated numbers (`REG-YYYY-NNNN`), types (local FS/tax return/statutory/regulatory/custom), filing reference tracking, structured report data (JSONField)

#### IC Transaction Workflow

```
Draft → Confirm → Confirmed → Post → Posted (creates paired Journal Entries)
                                    → Cancel → Cancelled
```

#### Consolidation Workflow

```
Draft → Execute → In Progress → Completed (creates elimination JEs + NCI records)
                               → Failed
Completed → Reverse → Reversed (creates contra JEs)
```

#### GL Integration

When an IC transaction is posted, `services.py` creates paired journal entries:
- **From entity JE**: Debit IC Receivable, Credit IC Revenue/Transfer
- **To entity JE**: Debit IC Expense/Transfer, Credit IC Payable

When consolidation runs, elimination entries create journal entries:
- **Debit**: Elimination rule debit account (e.g., IC Payable)
- **Credit**: Elimination rule credit account (e.g., IC Receivable)

When a GAAP adjustment is posted:
- **Debit**: Adjustment debit account
- **Credit**: Adjustment credit account

### 15. `tax` — Tax Management Module

Full tax compliance and planning with 7 submodules, 22 models, 48 views, and 40 templates.

- **TaxJurisdiction** — Hierarchical tax jurisdictions with levels (Federal → State → County → City → Special District), self-referential parent-child structure, country/state code classification
- **TaxRate** — Effective-dated tax rates per jurisdiction with compound rate support, priority-based calculation order, GL account mapping (tax collected/tax paid)
- **TaxRule** — Product/service taxability rules per jurisdiction with types (exempt/reduced/zero-rated/standard/surtax), product category matching, optional rate overrides
- **TaxGroup** — Combined tax rate groups aggregating multiple jurisdiction rates for single-calculation lookups (e.g., CA State + LA County + SF District)
- **TaxGroupMember** — Junction table linking tax rates to groups with priority ordering
- **TaxReturn** — Tax return headers with auto-generated numbers (`TR-YYYY-NNNN`), types (Sales Tax/VAT/GST/Income Tax/Payroll Tax/Use Tax), status workflow (Draft → Calculated → Reviewed → Filed → Amended), financial totals, GL journal entry link
- **TaxReturnLine** — Individual return line items with GL account reference, taxable amount, tax amount, applied rate
- **TaxReturnPayment** — Payment tracking on tax returns with method (EFT/Check/Wire), GL journal entry creation on posting
- **UseTaxAssessment** — Purchase-level use tax tracking with auto-generated numbers (`UT-YYYY-NNNN`), vendor/bill cross-references to AP module, status workflow (Pending → Accrued → Paid → Exempt), GL accrual posting
- **UseTaxAccrual** — Period-level use tax accrual summaries with auto-generated numbers (`UTA-YYYY-NNNN`), aggregate posting to GL
- **IncomeTaxProvision** — Income tax provision with auto-generated numbers (`ITP-YYYY-NNNN`), provision types (current/deferred/total), statutory rate, computed tax, permanent/temporary differences, tax credits, current and deferred tax expense, effective tax rate calculation, status workflow (Draft → Calculated → Reviewed → Finalized)
- **DeferredTaxItem** — Temporary difference line items with book vs tax basis, deferred tax asset/liability classification, GL account mapping
- **ETRReconciliation** — Effective tax rate reconciliation lines showing rate impact and amount impact per reconciling item
- **TaxDeadline** — Filing deadline management with auto-generated numbers (`TD-YYYY-NNNN`), tax type classification, jurisdiction link, reminder configuration, recurring pattern support (monthly/quarterly/annual), status workflow (Upcoming → In Progress → Filed → Overdue → Extended)
- **TaxDeadlineReminder** — Reminder log entries per deadline with sent status tracking
- **TaxAudit** — Tax audit tracking with auto-generated numbers (`TA-YYYY-NNNN`), auditing authority, audit period, status workflow (Pending → In Progress → Responded → Closed No Change → Closed Adjustment → Appealed), proposed vs agreed adjustment tracking, GL posting for adjustments
- **AuditFinding** — Individual audit findings with proposed/agreed amounts, status (Open → Agreed → Disputed → Resolved), response documentation
- **AuditDocument** — File attachments for audits with document type classification (notice/correspondence/workpaper/supporting/response/assessment)
- **NexusJurisdiction** — Economic nexus monitoring per jurisdiction with nexus type (physical/economic/affiliate/click-through), registration tracking, sales and transaction threshold monitoring with auto-calculated percentage
- **NexusActivity** — Period-level nexus activity records with sales amounts and transaction counts for threshold tracking

#### Tax Return Workflow

```
Draft → Calculate → Calculated → Review → Reviewed → File → Filed
                                                            → Amend → Amended
```

#### Income Tax Provision Workflow

```
Draft → Calculate → Calculated → Review → Reviewed → Post → Finalized (creates GL JE)
```

#### GL Integration

When a tax return payment is recorded, `services.py` creates a posted journal entry:
- **Debit**: Tax Payable (liability account)
- **Credit**: Cash/Bank Account

When use tax is accrued:
- **Debit**: Use Tax Expense
- **Credit**: Use Tax Payable

When income tax provision is posted:
- **Debit**: Income Tax Expense (current + deferred)
- **Credit**: Current Tax Payable + Deferred Tax Liability

When a tax audit adjustment is posted:
- **Debit**: Tax Expense
- **Credit**: Tax Payable

### 16. `dashboard` — Dashboard & Analytics
- **DashboardWidgetConfig** — Per-user widget layout (position, visibility, span)
- **Alert** — System alerts with severity (info, warning, danger, success)
- Services for KPI calculations and cash flow data
- 9 widget types: KPI Cards, Cash Flow, Alerts, Quick Actions, Executive Summary, Revenue Chart, Expense Chart, Receivables Aging, Payables Aging

---

## Accounts Payable Permissions

| Codename | Description |
|----------|-------------|
| `view_ap` | View Accounts Payable module |
| `manage_ap` | Full AP management access |
| `create_bill` | Create vendor bills |
| `approve_bill` | Approve/reject bills |
| `create_payment` | Create payments |
| `void_payment` | Void completed payments |
| `manage_vendors` | Create/edit/deactivate vendors |
| `view_ap_reports` | View aging reports and discount opportunities |
| `manage_vendor_portal` | Manage vendor portal tokens and settings |

---

## Accounts Receivable Permissions

| Codename | Description |
|----------|-------------|
| `view_ar` | View Accounts Receivable module |
| `manage_ar` | Full AR management access |
| `create_invoice` | Create customer invoices |
| `approve_invoice` | Approve/reject invoices |
| `send_invoice` | Send invoices to customers |
| `create_receipt` | Create receipts (incoming payments) |
| `void_receipt` | Void completed receipts |
| `manage_customers` | Create/edit/deactivate customers |
| `view_ar_reports` | View AR aging reports |
| `manage_collections` | Manage collection activities and dunning |
| `approve_write_off` | Approve bad debt write-offs |
| `manage_credit` | Manage credit limits and holds |
| `manage_recurring` | Manage recurring invoice templates |
| `manage_customer_portal` | Manage customer portal tokens and settings |

---

## Cash Management Permissions

| Codename | Description |
|----------|-------------|
| `view_bank` | View Cash Management module |
| `manage_bank` | Full bank account management access |
| `manage_bank_feeds` | Manage bank feed connections |
| `view_cash_position` | View cash position dashboard |
| `manage_forecasts` | Create/edit cash forecasts |
| `manage_transfers` | Create intercompany transfers |
| `approve_transfers` | Approve intercompany transfers |
| `view_bank_fees` | View bank fee analysis |

---

## Fixed Assets Permissions

| Codename | Description |
|----------|-------------|
| `view_assets` | View Fixed Assets module |
| `manage_assets` | Full fixed assets management access |

---

## Inventory & Cost Management Permissions

| Codename | Description |
|----------|-------------|
| `view_inventory` | View Inventory & Cost Management module |
| `manage_inventory` | Full inventory management access |

---

## Payroll Permissions

| Codename | Description |
|----------|-------------|
| `view_payroll` | View Payroll module |
| `manage_payroll` | Full payroll management access |

---

## Project/Job Costing Permissions

| Codename | Description |
|----------|-------------|
| `view_projects` | View Project/Job Costing module |
| `manage_projects` | Full project costing management access |

---

## Multi-Entity & Consolidation Permissions

| Codename | Description |
|----------|-------------|
| `view_multi_entity` | View Multi-Entity & Consolidation module |
| `manage_multi_entity` | Full multi-entity management access |

---

## Frontend & Theming

### Layout System

Three layout variants controlled via `data-layout` attribute on `<html>`:

| Layout | Description |
|--------|-------------|
| **Vertical** | Traditional sidebar + main content (default) |
| **Horizontal** | Top navigation bar + content |
| **Detached** | Contained/card-based layout |

### Theme Features

| Feature | Implementation |
|---------|---------------|
| Light/Dark mode | Bootstrap 5.3 `data-bs-theme`, CSS variables, localStorage |
| Sidebar variants | Default, colored, gradient backgrounds |
| Width | Fluid or boxed container |
| Position | Fixed or scrollable sidebar/topbar |
| RTL support | Dedicated `rtl.css` stylesheet |
| Preloader | Animated loading screen on page load |
| Theme persistence | All preferences saved to localStorage |
| OS preference | Auto-detects `prefers-color-scheme` |

### Static Files

| Directory | Files | Purpose |
|-----------|-------|---------|
| `static/css/` | 8 files | Theme variables, app styles, layouts, dark mode, RTL |
| `static/js/` | 7 files | Theme switching, layout management, dashboard charts |
| `static/images/` | — | Logos, avatar placeholders, auth backgrounds |

### Right Sidebar Settings Panel

An offcanvas panel accessible from the topbar allows users to customize:
- Layout mode (vertical / horizontal / detached)
- Color scheme (light / dark)
- Container width (fluid / boxed)
- Sidebar color (default / colored)
- Topbar position (fixed / scrollable)

---

## Role-Based Access Control

### System Roles (created per tenant by seeder)

| Role | Permissions |
|------|-------------|
| **Admin** | Full access — all 25 permissions |
| **Manager** | Everything except `admin_full` |
| **Accountant** | Dashboard, GL, AP, AR module permissions |
| **Viewer** | All `view_*` permissions only (read-only) |

### Permission Modules

Permissions are organized by module:
- `dashboard` — view_dashboard, manage_dashboard
- `users` — view_users, manage_users, invite_users
- `roles` — view_roles, manage_roles
- `company` — view_company, manage_company
- `coa` — view_coa, manage_coa
- `journal` — view_journal, create_journal, approve_journal
- `general_ledger` — post_journal, manage_coa_accounts, manage_periods, reconcile_accounts, manage_allocations, run_allocations, view_audit_trail, manage_exchange_rates
- `accounts_payable` — view_ap, manage_ap, create_bill, approve_bill, create_payment, void_payment, manage_vendors, view_ap_reports, manage_vendor_portal
- `ar` — view_ar, manage_ar, create_invoice, approve_invoice, send_invoice, create_receipt, void_receipt, manage_customers, view_ar_reports, manage_collections, approve_write_off, manage_credit, manage_recurring, manage_customer_portal
- `bank` — view_bank, manage_bank, manage_bank_feeds, view_cash_position, manage_forecasts, manage_transfers, approve_transfers, view_bank_fees
- `fixed_assets` — view_assets, manage_assets
- `inventory` — view_inventory, manage_inventory
- `payroll` — view_payroll, manage_payroll
- `project_costing` — view_projects, manage_projects
- `multi_entity` — view_multi_entity, manage_multi_entity
- `admin` — admin_full

### Access Control Decorators

```python
from apps.accounts.decorators import tenant_required, role_required, permission_required

@tenant_required
def my_view(request, tenant_slug):
    ...

@role_required('Admin', 'Manager')
def admin_view(request, tenant_slug):
    ...

@permission_required('manage_coa_accounts', 'post_journal')
def gl_view(request, tenant_slug):
    ...
```

---

## Future Modules

The application is architected to support these additional accounting modules:

| Module | Description |
|--------|-------------|
| Reporting | Financial statements, custom report builder, XBRL |
| Budgeting | Budget creation, variance analysis, forecasting |

---

## License

This project is proprietary. All rights reserved.
