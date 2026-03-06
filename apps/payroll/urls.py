from django.urls import path

from .views import (
    employees, payroll_journal, tax_management,
    benefits, garnishments, workers_comp, reconciliation,
)

app_name = 'payroll'

urlpatterns = [
    # -------------------------------------------------------------------------
    # Employee Master
    # -------------------------------------------------------------------------
    path('employees/', employees.employee_list, name='employee_list'),
    path('employees/create/', employees.employee_create, name='employee_create'),
    path('employees/<int:pk>/', employees.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', employees.employee_edit, name='employee_edit'),

    # -------------------------------------------------------------------------
    # Payroll Journal
    # -------------------------------------------------------------------------
    path('journals/', payroll_journal.journal_list, name='journal_list'),
    path('journals/create/', payroll_journal.journal_create, name='journal_create'),
    path('journals/<int:pk>/', payroll_journal.journal_detail, name='journal_detail'),
    path('journals/<int:pk>/calculate/', payroll_journal.journal_calculate, name='journal_calculate'),
    path('journals/<int:pk>/approve/', payroll_journal.journal_approve, name='journal_approve'),
    path('journals/<int:pk>/post/', payroll_journal.journal_post, name='journal_post'),

    # -------------------------------------------------------------------------
    # Tax Management
    # -------------------------------------------------------------------------
    path('tax-withholdings/', tax_management.tax_withholding_list, name='tax_withholding_list'),
    path('tax-withholdings/create/', tax_management.tax_withholding_create, name='tax_withholding_create'),
    path('tax-withholdings/<int:pk>/edit/', tax_management.tax_withholding_edit, name='tax_withholding_edit'),

    path('remittances/', tax_management.remittance_list, name='remittance_list'),
    path('remittances/create/', tax_management.remittance_create, name='remittance_create'),
    path('remittances/<int:pk>/', tax_management.remittance_detail, name='remittance_detail'),
    path('remittances/<int:pk>/pay/', tax_management.remittance_pay, name='remittance_pay'),

    # -------------------------------------------------------------------------
    # Benefits
    # -------------------------------------------------------------------------
    path('benefits/', benefits.benefit_plan_list, name='benefit_plan_list'),
    path('benefits/create/', benefits.benefit_plan_create, name='benefit_plan_create'),
    path('benefits/<int:pk>/', benefits.benefit_plan_detail, name='benefit_plan_detail'),
    path('benefits/<int:pk>/edit/', benefits.benefit_plan_edit, name='benefit_plan_edit'),
    path('benefits/enroll/', benefits.enrollment_create, name='enrollment_create'),
    path('benefits/enroll/<int:pk>/edit/', benefits.enrollment_edit, name='enrollment_edit'),

    # -------------------------------------------------------------------------
    # Garnishments
    # -------------------------------------------------------------------------
    path('garnishments/', garnishments.garnishment_list, name='garnishment_list'),
    path('garnishments/create/', garnishments.garnishment_create, name='garnishment_create'),
    path('garnishments/<int:pk>/', garnishments.garnishment_detail, name='garnishment_detail'),
    path('garnishments/<int:pk>/edit/', garnishments.garnishment_edit, name='garnishment_edit'),

    # -------------------------------------------------------------------------
    # Workers Comp
    # -------------------------------------------------------------------------
    path('workers-comp/', workers_comp.comp_class_list, name='comp_class_list'),
    path('workers-comp/create/', workers_comp.comp_class_create, name='comp_class_create'),
    path('workers-comp/<int:pk>/', workers_comp.comp_class_detail, name='comp_class_detail'),
    path('workers-comp/<int:pk>/edit/', workers_comp.comp_class_edit, name='comp_class_edit'),
    path('workers-comp/assign/', workers_comp.assignment_create, name='assignment_create'),
    path('workers-comp/assign/<int:pk>/edit/', workers_comp.assignment_edit, name='assignment_edit'),

    # -------------------------------------------------------------------------
    # Payroll Reconciliation
    # -------------------------------------------------------------------------
    path('reconciliation/', reconciliation.reconciliation_list, name='reconciliation_list'),
    path('reconciliation/create/', reconciliation.reconciliation_create, name='reconciliation_create'),
    path('reconciliation/<int:pk>/', reconciliation.reconciliation_detail, name='reconciliation_detail'),
]
