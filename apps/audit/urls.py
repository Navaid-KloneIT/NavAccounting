from django.urls import path

from .views import (
    sox_controls, sod, access_controls, change_management,
    audit_trail, exceptions, documents,
)

app_name = 'audit'

urlpatterns = [
    # ── SOX Controls ─────────────────────────
    path('sox/', sox_controls.sox_control_list, name='sox_control_list'),
    path('sox/create/', sox_controls.sox_control_create, name='sox_control_create'),
    path('sox/<int:pk>/', sox_controls.sox_control_detail, name='sox_control_detail'),
    path('sox/<int:pk>/edit/', sox_controls.sox_control_edit, name='sox_control_edit'),
    path('sox/<int:pk>/add-test/', sox_controls.sox_test_create, name='sox_test_create'),

    # ── Segregation of Duties ────────────────
    path('sod/rules/', sod.sod_rule_list, name='sod_rule_list'),
    path('sod/rules/create/', sod.sod_rule_create, name='sod_rule_create'),
    path('sod/rules/<int:pk>/', sod.sod_rule_detail, name='sod_rule_detail'),
    path('sod/rules/<int:pk>/edit/', sod.sod_rule_edit, name='sod_rule_edit'),
    path('sod/violations/', sod.sod_violation_list, name='sod_violation_list'),
    path('sod/violations/<int:pk>/', sod.sod_violation_detail, name='sod_violation_detail'),
    path('sod/violations/<int:pk>/resolve/', sod.sod_violation_resolve, name='sod_violation_resolve'),
    path('sod/scan/', sod.sod_scan, name='sod_scan'),

    # ── Access Controls ──────────────────────
    path('access/policies/', access_controls.access_policy_list, name='access_policy_list'),
    path('access/policies/create/', access_controls.access_policy_create, name='access_policy_create'),
    path('access/policies/<int:pk>/', access_controls.access_policy_detail, name='access_policy_detail'),
    path('access/policies/<int:pk>/edit/', access_controls.access_policy_edit, name='access_policy_edit'),
    path('access/reviews/', access_controls.access_review_list, name='access_review_list'),
    path('access/reviews/create/', access_controls.access_review_create, name='access_review_create'),
    path('access/reviews/<int:pk>/', access_controls.access_review_detail, name='access_review_detail'),
    path('access/reviews/<int:pk>/edit/', access_controls.access_review_edit, name='access_review_edit'),

    # ── Change Management ────────────────────
    path('changes/', change_management.change_request_list, name='change_request_list'),
    path('changes/create/', change_management.change_request_create, name='change_request_create'),
    path('changes/<int:pk>/', change_management.change_request_detail, name='change_request_detail'),
    path('changes/<int:pk>/edit/', change_management.change_request_edit, name='change_request_edit'),
    path('changes/<int:pk>/submit/', change_management.change_request_submit, name='change_request_submit'),
    path('changes/<int:pk>/approve/', change_management.change_request_approve, name='change_request_approve'),
    path('changes/<int:pk>/reject/', change_management.change_request_reject, name='change_request_reject'),
    path('changes/<int:pk>/implement/', change_management.change_request_implement, name='change_request_implement'),

    # ── Audit Trail ──────────────────────────
    path('trail/', audit_trail.audit_entry_list, name='audit_entry_list'),
    path('trail/<int:pk>/', audit_trail.audit_entry_detail, name='audit_entry_detail'),

    # ── Exception Reporting ──────────────────
    path('exceptions/rules/', exceptions.exception_rule_list, name='exception_rule_list'),
    path('exceptions/rules/create/', exceptions.exception_rule_create, name='exception_rule_create'),
    path('exceptions/rules/<int:pk>/', exceptions.exception_rule_detail, name='exception_rule_detail'),
    path('exceptions/rules/<int:pk>/edit/', exceptions.exception_rule_edit, name='exception_rule_edit'),
    path('exceptions/', exceptions.exception_list, name='exception_list'),
    path('exceptions/<int:pk>/', exceptions.exception_detail, name='exception_detail'),
    path('exceptions/<int:pk>/resolve/', exceptions.exception_resolve, name='exception_resolve'),
    path('exceptions/run-scan/', exceptions.exception_run_scan, name='exception_run_scan'),

    # ── Document Management ──────────────────
    path('documents/categories/', documents.document_category_list, name='document_category_list'),
    path('documents/categories/create/', documents.document_category_create, name='document_category_create'),
    path('documents/categories/<int:pk>/edit/', documents.document_category_edit, name='document_category_edit'),
    path('documents/', documents.document_list, name='document_list'),
    path('documents/upload/', documents.document_upload, name='document_upload'),
    path('documents/<int:pk>/', documents.document_detail, name='document_detail'),
    path('documents/<int:pk>/edit/', documents.document_edit, name='document_edit'),
    path('documents/<int:pk>/download/', documents.document_download, name='document_download'),
]
