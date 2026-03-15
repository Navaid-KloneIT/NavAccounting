from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.tenants.managers import set_current_tenant

from ..forms import XBRLFilingForm, XBRLTagFormSet, FilingDocumentForm
from ..models import XBRLFiling


@login_required
def filing_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = XBRLFiling.objects.filter(tenant=tenant)

    # Stats
    total_count = qs.count()
    draft_count = qs.filter(status='draft').count()
    submitted_count = qs.filter(status='submitted').count()
    accepted_count = qs.filter(status='accepted').count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(filing_number__icontains=search) | Q(name__icontains=search) |
            Q(cik_number__icontains=search)
        )

    # Type filter
    filing_type = request.GET.get('type', '')
    if filing_type:
        qs = qs.filter(filing_type=filing_type)

    # Status filter
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reporting/xbrl_filing/filing_list.html', {
        'filings': page_obj,
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'submitted_count': submitted_count,
        'accepted_count': accepted_count,
        'type_choices': XBRLFiling.FILING_TYPE_CHOICES,
        'status_choices': XBRLFiling.STATUS_CHOICES,
    })


@login_required
def filing_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = XBRLFilingForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.created_by = request.user
            obj.save()
            messages.success(request, f'XBRL filing "{obj.filing_number}" created.')
            return redirect('reporting:filing_detail', tenant_slug=tenant.slug, pk=obj.pk)
    else:
        form = XBRLFilingForm(tenant=tenant)

    return render(request, 'reporting/xbrl_filing/filing_form.html', {
        'form': form,
        'is_create': True,
    })


@login_required
def filing_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    filing = get_object_or_404(XBRLFiling, pk=pk, tenant=tenant)
    tags = filing.tags.all()
    documents = filing.documents.all()

    return render(request, 'reporting/xbrl_filing/filing_detail.html', {
        'filing': filing,
        'tags': tags,
        'documents': documents,
    })


@login_required
def filing_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    filing = get_object_or_404(XBRLFiling, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = XBRLFilingForm(request.POST, instance=filing, tenant=tenant)
        tag_formset = XBRLTagFormSet(request.POST, instance=filing)
        if form.is_valid() and tag_formset.is_valid():
            form.save()
            tags = tag_formset.save(commit=False)
            for tag in tags:
                tag.tenant = tenant
                tag.save()
            for tag in tag_formset.deleted_objects:
                tag.delete()
            messages.success(request, f'Filing "{filing.filing_number}" updated.')
            return redirect('reporting:filing_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = XBRLFilingForm(instance=filing, tenant=tenant)
        tag_formset = XBRLTagFormSet(instance=filing)

    return render(request, 'reporting/xbrl_filing/filing_form.html', {
        'form': form,
        'tag_formset': tag_formset,
        'filing': filing,
        'is_create': False,
    })


@login_required
def filing_validate(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    filing = get_object_or_404(XBRLFiling, pk=pk, tenant=tenant)
    if filing.status in ('draft', 'tagging'):
        filing.status = 'validated'
        filing.save()
        messages.success(request, f'Filing "{filing.filing_number}" validated.')
    else:
        messages.warning(request, 'Filing can only be validated from draft or tagging status.')

    return redirect('reporting:filing_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def filing_submit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    filing = get_object_or_404(XBRLFiling, pk=pk, tenant=tenant)
    if filing.status == 'validated':
        filing.status = 'submitted'
        filing.submitted_at = timezone.now()
        filing.save()
        messages.success(request, f'Filing "{filing.filing_number}" submitted.')
    else:
        messages.warning(request, 'Filing must be validated before submission.')

    return redirect('reporting:filing_detail', tenant_slug=tenant.slug, pk=pk)


@login_required
def document_upload(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    filing = get_object_or_404(XBRLFiling, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = FilingDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.tenant = tenant
            doc.filing = filing
            doc.uploaded_by = request.user
            if doc.file:
                doc.file_size = doc.file.size
            doc.save()
            messages.success(request, f'Document "{doc.name}" uploaded.')
            return redirect('reporting:filing_detail', tenant_slug=tenant.slug, pk=pk)
    else:
        form = FilingDocumentForm()

    return render(request, 'reporting/xbrl_filing/document_upload.html', {
        'form': form,
        'filing': filing,
    })
