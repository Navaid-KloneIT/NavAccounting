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
| `/t/<slug>/` | Tenant-scoped routes (dashboard, company, users, roles, GL, AP, AR, CM) |
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

### 10. `dashboard` — Dashboard & Analytics
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
- `assets` — view_assets, manage_assets
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
| Fixed Assets | Asset register, depreciation, disposals |
| Inventory | Item master, valuation (FIFO/LIFO), purchase orders |
| Tax | Sales tax engine, tax returns, compliance |
| Reporting | Financial statements, custom report builder, XBRL |
| Budgeting | Budget creation, variance analysis, forecasting |

---

## License

This project is proprietary. All rights reserved.
