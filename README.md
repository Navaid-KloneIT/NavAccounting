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
- **Chart of Accounts** — Pre-built COA templates with hierarchical account structure
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
│   └── dashboard/                  # Widget config, Alerts, KPI services
├── templates/
│   ├── base.html                   # Root HTML template
│   ├── layouts/                    # vertical, horizontal, detached
│   ├── partials/                   # _topbar, _sidebar, _footer, _preloader, etc.
│   ├── accounts/                   # Login, register, forgot password, profile
│   ├── dashboard/                  # Dashboard index + widget partials
│   ├── company/                    # Company setup, fiscal years, COA
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
```

### What Gets Seeded

| Category | Data |
|----------|------|
| Currencies | 30 currencies (USD, EUR, GBP, JPY, etc.) with ISO 4217 codes |
| Account Types | 5 types — Asset, Liability, Equity, Revenue, Expense |
| Permissions | 25 module-based permissions (view/manage dashboard, users, roles, etc.) |
| COA Template | "Standard Business" template with 61 hierarchical accounts |
| Tenants | 3 organizations — Acme Corporation, TechStart Solutions, Green Valley Farms |
| Users | Superuser + 10 users per tenant (managers, accountants, viewers) |
| Roles | 4 system roles per tenant — Admin, Manager, Accountant, Viewer |
| Company Settings | Company info, fiscal years (2025-2026), 12 monthly periods |
| Dashboard | 12 alerts + 5 widget configurations per tenant |

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
- `/static/`, `/media/` — Static assets

### System-Wide vs Tenant-Scoped Models

| System-Wide (no tenant) | Tenant-Scoped |
|--------------------------|---------------|
| CustomUser | UserProfile, UserInvitation |
| Tenant, TenantMembership | CompanySettings, FiscalYear, FiscalPeriod |
| Currency, AccountType | Role, TenantUserRole |
| Permission | DashboardWidgetConfig, Alert |
| ChartOfAccountsTemplate | — |

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
| `/t/<slug>/` | Tenant-scoped routes (dashboard, company, users, roles) |
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

### 6. `dashboard` — Dashboard & Analytics
- **DashboardWidgetConfig** — Per-user widget layout (position, visibility, span)
- **Alert** — System alerts with severity (info, warning, danger, success)
- Services for KPI calculations and cash flow data
- 9 widget types: KPI Cards, Cash Flow, Alerts, Quick Actions, Executive Summary, Revenue Chart, Expense Chart, Receivables Aging, Payables Aging

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
- `ap` — view_ap, manage_ap
- `ar` — view_ar, manage_ar
- `bank` — view_bank, manage_bank
- `assets` — view_assets, manage_assets
- `admin` — admin_full

### Access Control Decorators

```python
from apps.tenants.decorators import tenant_required, role_required

@tenant_required
def my_view(request, tenant_slug):
    ...

@role_required('Admin', 'Manager')
def admin_view(request, tenant_slug):
    ...
```

---

## Future Modules

The application is architected to support these additional accounting modules:

| Module | Description |
|--------|-------------|
| General Ledger | Journal entries, period close, account reconciliation |
| Accounts Payable | Vendor management, bill processing, payment scheduling |
| Accounts Receivable | Customer management, invoicing, collections |
| Cash Management | Bank feeds, reconciliation, cash positioning |
| Fixed Assets | Asset register, depreciation, disposals |
| Inventory | Item master, valuation (FIFO/LIFO), purchase orders |
| Tax | Sales tax engine, tax returns, compliance |
| Reporting | Financial statements, custom report builder, XBRL |
| Budgeting | Budget creation, variance analysis, forecasting |
| Audit & Controls | SOX controls, segregation of duties, audit trail |

---

## License

This project is proprietary. All rights reserved.
