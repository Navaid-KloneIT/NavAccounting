from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.tenants.managers import set_current_tenant
from ..forms import DocumentCategoryForm, DocumentForm
from ..models import DocumentCategory, Document
from ..services import auto_populate_document_metadata


# ──────────────────────────────────────────────
# Document Categories
# ──────────────────────────────────────────────

@login_required
def document_category_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = DocumentCategory.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search))

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_categories = DocumentCategory.objects.filter(tenant=tenant)
    return render(request, 'audit/documents/document_category_list.html', {
        'categories': page_obj,
        'page_obj': page_obj,
        'total_count': all_categories.count(),
    })


@login_required
def document_category_create(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = DocumentCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = tenant
            category.category_number = DocumentCategory.generate_category_number(tenant)
            category.save()
            messages.success(request, f'Document category "{category.name}" created.')
            return redirect('audit:document_category_list', tenant_slug=tenant.slug)
    else:
        form = DocumentCategoryForm()

    return render(request, 'audit/documents/document_category_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def document_category_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    category = get_object_or_404(DocumentCategory.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = DocumentCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Document category "{category.name}" updated.')
            return redirect('audit:document_category_list', tenant_slug=tenant.slug)
    else:
        form = DocumentCategoryForm(instance=category)

    return render(request, 'audit/documents/document_category_form.html', {
        'form': form, 'is_edit': True, 'category': category,
    })


# ──────────────────────────────────────────────
# Documents
# ──────────────────────────────────────────────

@login_required
def document_list(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    qs = Document.objects.filter(tenant=tenant)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(document_number__icontains=search) |
            Q(title__icontains=search) |
            Q(tags__icontains=search)
        )

    category_filter = request.GET.get('category', '')
    if category_filter:
        qs = qs.filter(category_id=category_filter)

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    all_documents = Document.objects.filter(tenant=tenant)
    return render(request, 'audit/documents/document_list.html', {
        'documents': page_obj,
        'page_obj': page_obj,
        'total_count': all_documents.count(),
        'active_count': all_documents.filter(status='active').count(),
        'archived_count': all_documents.filter(status='archived').count(),
        'categories': DocumentCategory.objects.filter(tenant=tenant),
        'status_choices': Document.STATUS_CHOICES,
    })


@login_required
def document_upload(request, tenant_slug):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, tenant=tenant)
        if form.is_valid():
            document = form.save(commit=False)
            document.tenant = tenant
            document.document_number = Document.generate_document_number(tenant)
            document.uploaded_by = request.user
            document.save()
            auto_populate_document_metadata(document)
            messages.success(request, f'Document "{document.title}" uploaded.')
            return redirect('audit:document_detail', tenant_slug=tenant.slug, pk=document.pk)
    else:
        form = DocumentForm(tenant=tenant)

    return render(request, 'audit/documents/document_form.html', {
        'form': form, 'is_edit': False,
    })


@login_required
def document_detail(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    document = get_object_or_404(Document.unscoped, pk=pk, tenant=tenant)

    return render(request, 'audit/documents/document_detail.html', {
        'document': document,
    })


@login_required
def document_edit(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    document = get_object_or_404(Document.unscoped, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document, tenant=tenant)
        if form.is_valid():
            form.save()
            auto_populate_document_metadata(document)
            messages.success(request, f'Document "{document.title}" updated.')
            return redirect('audit:document_detail', tenant_slug=tenant.slug, pk=document.pk)
    else:
        form = DocumentForm(instance=document, tenant=tenant)

    return render(request, 'audit/documents/document_form.html', {
        'form': form, 'is_edit': True, 'document': document,
    })


@login_required
def document_download(request, tenant_slug, pk):
    tenant = request.tenant
    if not tenant:
        return redirect('tenants:select')
    set_current_tenant(tenant)

    document = get_object_or_404(Document.unscoped, pk=pk, tenant=tenant)
    filename = document.file_name or document.file.name.split('/')[-1]

    return FileResponse(document.file.open(), as_attachment=True, filename=filename)
