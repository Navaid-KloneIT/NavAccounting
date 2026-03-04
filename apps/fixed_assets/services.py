from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from apps.general_ledger.models import JournalEntry, JournalEntryLine


def calculate_straight_line_depreciation(asset, period_start, period_end):
    """
    Calculate straight-line depreciation for a given period.
    Monthly amount = (cost - salvage) / useful_life_months
    Pro-rated for partial periods.
    """
    depreciable_amount = asset.acquisition_cost - asset.salvage_value
    if asset.useful_life_months <= 0 or depreciable_amount <= 0:
        return Decimal('0.00')

    monthly_amount = (depreciable_amount / asset.useful_life_months).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    # Calculate months in this period
    months = _months_between(period_start, period_end)

    amount = (monthly_amount * Decimal(str(months))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    # Don't exceed remaining depreciable amount
    remaining = depreciable_amount - asset.accumulated_depreciation
    return min(amount, max(remaining, Decimal('0.00')))


def calculate_declining_balance_depreciation(asset, period_start, period_end, rate=None):
    """
    Calculate declining balance depreciation for a given period.
    Period amount = NBV * (rate / 12) * months_in_period
    Default rate is 200% (double declining balance).
    """
    if rate is None:
        try:
            rate = asset.depreciation_profile.declining_balance_rate
        except Exception:
            rate = Decimal('200.00')

    nbv = asset.net_book_value
    if nbv <= asset.salvage_value:
        return Decimal('0.00')

    annual_rate = rate / Decimal('100')
    monthly_rate = annual_rate / Decimal('12')
    months = _months_between(period_start, period_end)

    amount = (nbv * monthly_rate * Decimal(str(months))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    # Don't depreciate below salvage value
    max_depreciation = nbv - asset.salvage_value
    return min(amount, max(max_depreciation, Decimal('0.00')))


def calculate_units_of_production_depreciation(asset, units_used):
    """
    Calculate units-of-production depreciation.
    Amount = (cost - salvage) / total_units * units_used
    """
    try:
        profile = asset.depreciation_profile
        total_units = profile.total_units or 0
    except Exception:
        return Decimal('0.00')

    if total_units <= 0:
        return Decimal('0.00')

    depreciable_amount = asset.acquisition_cost - asset.salvage_value
    per_unit = depreciable_amount / Decimal(str(total_units))
    amount = (per_unit * Decimal(str(units_used))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    remaining = depreciable_amount - asset.accumulated_depreciation
    return min(amount, max(remaining, Decimal('0.00')))


def generate_depreciation_schedule(asset):
    """
    Generate the full depreciation schedule for an asset.
    Creates DepreciationSchedule rows for each month.
    """
    from .models import DepreciationSchedule

    # Clear existing unposted schedule lines
    DepreciationSchedule.unscoped.filter(
        asset=asset, is_posted=False
    ).delete()

    depreciable_amount = asset.acquisition_cost - asset.salvage_value
    if depreciable_amount <= 0 or asset.useful_life_months <= 0:
        return []

    monthly_amount = (depreciable_amount / asset.useful_life_months).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    schedules = []
    accumulated = asset.accumulated_depreciation
    current_date = asset.acquisition_date

    for period_num in range(1, asset.useful_life_months + 1):
        period_start = current_date
        # Move to next month
        if current_date.month == 12:
            next_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            next_date = current_date.replace(month=current_date.month + 1)
        period_end = next_date - __import__('datetime').timedelta(days=1)

        # Last period gets remainder to avoid rounding errors
        if period_num == asset.useful_life_months:
            dep_amount = depreciable_amount - (accumulated - asset.accumulated_depreciation)
        else:
            dep_amount = monthly_amount

        accumulated_new = accumulated + dep_amount
        nbv = asset.acquisition_cost - accumulated_new

        schedule = DepreciationSchedule(
            tenant=asset.tenant,
            asset=asset,
            period_number=period_num,
            period_start=period_start,
            period_end=period_end,
            depreciation_amount=dep_amount,
            accumulated_depreciation=accumulated_new,
            net_book_value=nbv,
        )
        schedules.append(schedule)
        accumulated = accumulated_new
        current_date = next_date

    DepreciationSchedule.unscoped.bulk_create(schedules)
    return schedules


def run_depreciation(tenant, fiscal_period, user):
    """
    Run batch depreciation for all eligible assets in a fiscal period.
    Creates a DepreciationEntry and posts a GL journal entry.
    """
    from .models import Asset, DepreciationEntry, DepreciationSchedule

    # Find unposted schedule lines within this period
    schedules = DepreciationSchedule.unscoped.filter(
        tenant=tenant,
        is_posted=False,
        period_start__gte=fiscal_period.start_date,
        period_end__lte=fiscal_period.end_date,
    ).select_related('asset', 'asset__category')

    if not schedules.exists():
        return None

    total_amount = Decimal('0.00')
    asset_ids = set()
    schedule_list = list(schedules)

    for schedule in schedule_list:
        total_amount += schedule.depreciation_amount
        asset_ids.add(schedule.asset_id)

    # Create depreciation entry
    entry = DepreciationEntry.unscoped.create(
        tenant=tenant,
        entry_number=DepreciationEntry.generate_entry_number(tenant),
        run_date=timezone.now().date(),
        fiscal_period=fiscal_period,
        total_amount=total_amount,
        asset_count=len(asset_ids),
        status='posted',
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Create GL journal entry
    je = _create_depreciation_journal_entry(
        tenant, fiscal_period, schedule_list, total_amount, user
    )
    entry.journal_entry = je
    entry.save(update_fields=['journal_entry'])

    # Mark schedules as posted and update asset accumulated depreciation
    for schedule in schedule_list:
        schedule.is_posted = True
        schedule.journal_entry = je
        schedule.save(update_fields=['is_posted', 'journal_entry'])

        # Update asset accumulated depreciation
        asset = schedule.asset
        asset.accumulated_depreciation += schedule.depreciation_amount
        asset.save(update_fields=['accumulated_depreciation', 'updated_at'])

    return entry


def _create_depreciation_journal_entry(tenant, fiscal_period, schedules, total_amount, user):
    """Create GL journal entry for depreciation run."""
    from .models import Asset

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=timezone.now().date(),
        description=f"Fixed Asset Depreciation - {fiscal_period}",
        reference=f"FA-DEP-{fiscal_period}",
        fiscal_period=fiscal_period,
        status='posted',
        source='fa_depreciation',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Group by category for consolidated journal lines
    category_totals = {}
    for schedule in schedules:
        cat = schedule.asset.category
        if cat.id not in category_totals:
            category_totals[cat.id] = {
                'category': cat,
                'amount': Decimal('0.00'),
            }
        category_totals[cat.id]['amount'] += schedule.depreciation_amount

    for cat_data in category_totals.values():
        cat = cat_data['category']
        amount = cat_data['amount']

        # Debit: Depreciation Expense
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=cat.depreciation_gl_account,
            description=f"Depreciation expense - {cat.name}",
            debit=amount,
            credit=Decimal('0.00'),
        )

        # Credit: Accumulated Depreciation
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=cat.accumulated_depreciation_gl_account,
            description=f"Accumulated depreciation - {cat.name}",
            debit=Decimal('0.00'),
            credit=amount,
        )

    return je


def create_acquisition_journal_entry(acquisition, tenant, user):
    """
    Create GL journal entry for asset acquisition.
    Debit: Asset GL Account (from category)
    Credit: AP/Cash account (from acquisition)
    """
    asset = acquisition.asset
    category = asset.category

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=acquisition.acquisition_date,
        description=f"Asset Acquisition: {asset.asset_number} - {asset.name}",
        reference=acquisition.acquisition_number,
        status='posted',
        source='fa_acquisition',
        currency=acquisition.currency,
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit: Asset account
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=category.asset_gl_account,
        description=f"Capitalize asset {asset.asset_number}",
        debit=acquisition.amount,
        credit=Decimal('0.00'),
    )

    # Credit: Same asset account (offset - actual AP/Cash entry handled by AP module)
    # In practice, the credit side depends on payment method
    # For now we credit the asset account as a placeholder
    # The AP bill or cash payment will handle the other side
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=category.asset_gl_account,
        description=f"Acquisition of {asset.asset_number}",
        debit=Decimal('0.00'),
        credit=acquisition.amount,
    )

    return je


def create_disposal_journal_entry(disposal, tenant, user):
    """
    Create GL journal entry for asset disposal.
    Removes asset from books and records gain/loss.
    """
    asset = disposal.asset
    category = asset.category

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=disposal.disposal_date,
        description=f"Asset Disposal: {asset.asset_number} - {asset.name}",
        reference=disposal.disposal_number,
        status='posted',
        source='fa_disposal',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit: Accumulated Depreciation (remove contra-asset)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=category.accumulated_depreciation_gl_account,
        description=f"Remove accumulated depreciation - {asset.asset_number}",
        debit=asset.accumulated_depreciation,
        credit=Decimal('0.00'),
    )

    # Credit: Asset Account (remove asset cost)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=category.asset_gl_account,
        description=f"Remove asset cost - {asset.asset_number}",
        debit=Decimal('0.00'),
        credit=asset.acquisition_cost,
    )

    # Record proceeds and gain/loss
    if disposal.proceeds > Decimal('0.00'):
        # Debit: Cash/AR for proceeds (use asset account as placeholder)
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.asset_gl_account,
            description=f"Disposal proceeds - {asset.asset_number}",
            debit=disposal.proceeds,
            credit=Decimal('0.00'),
        )

    # Gain or loss
    if disposal.gain_loss > Decimal('0.00'):
        # Gain on disposal (credit)
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.depreciation_gl_account,
            description=f"Gain on disposal - {asset.asset_number}",
            debit=Decimal('0.00'),
            credit=disposal.gain_loss,
        )
    elif disposal.gain_loss < Decimal('0.00'):
        # Loss on disposal (debit)
        JournalEntryLine.objects.create(
            journal_entry=je,
            account=category.depreciation_gl_account,
            description=f"Loss on disposal - {asset.asset_number}",
            debit=abs(disposal.gain_loss),
            credit=Decimal('0.00'),
        )

    return je


def create_impairment_journal_entry(impairment, tenant, user):
    """
    Create GL journal entry for impairment loss.
    Debit: Impairment Loss (use depreciation expense account)
    Credit: Accumulated Depreciation
    """
    asset = impairment.asset
    category = asset.category

    je = JournalEntry.unscoped.create(
        tenant=tenant,
        entry_number=JournalEntry.generate_entry_number(tenant),
        date=impairment.test_date,
        description=f"Impairment Loss: {asset.asset_number} - {asset.name}",
        reference=f"IMP-{asset.asset_number}-{impairment.test_date}",
        status='posted',
        source='fa_impairment',
        currency_id=_get_default_currency_id(tenant),
        created_by=user,
        posted_by=user,
        posted_at=timezone.now(),
    )

    # Debit: Impairment Loss Expense
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=category.depreciation_gl_account,
        description=f"Impairment loss - {asset.asset_number}",
        debit=impairment.impairment_loss,
        credit=Decimal('0.00'),
    )

    # Credit: Accumulated Depreciation (increases contra-asset)
    JournalEntryLine.objects.create(
        journal_entry=je,
        account=category.accumulated_depreciation_gl_account,
        description=f"Impairment - {asset.asset_number}",
        debit=Decimal('0.00'),
        credit=impairment.impairment_loss,
    )

    return je


def calculate_disposal_gain_loss(asset, proceeds):
    """Calculate gain or loss on disposal."""
    nbv = asset.net_book_value
    return proceeds - nbv


def _months_between(start_date, end_date):
    """Calculate the number of months between two dates (approximate)."""
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    return max(months, 1)


def _get_default_currency_id(tenant):
    """Get the default currency for a tenant."""
    from apps.company.models import CompanySettings
    try:
        settings = CompanySettings.unscoped.filter(tenant=tenant).first()
        if settings and settings.default_currency_id:
            return settings.default_currency_id
    except Exception:
        pass
    from apps.company.models import Currency
    currency = Currency.objects.first()
    return currency.id if currency else 1
