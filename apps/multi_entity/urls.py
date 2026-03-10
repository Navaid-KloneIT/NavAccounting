from django.urls import path

from .views import (
    consolidation,
    entities,
    intercompany,
    regulatory,
    transfer_pricing,
    translation,
)

app_name = 'multi_entity'

urlpatterns = [
    # === Entity Management ===
    path('entities/', entities.entity_list, name='entity_list'),
    path('entities/create/', entities.entity_create, name='entity_create'),
    path('entities/<int:pk>/', entities.entity_detail, name='entity_detail'),
    path('entities/<int:pk>/edit/', entities.entity_edit, name='entity_edit'),
    path('entities/hierarchy/', entities.entity_hierarchy, name='entity_hierarchy'),

    # === Inter-company Transactions ===
    path('ic-transactions/', intercompany.ic_transaction_list, name='ic_transaction_list'),
    path('ic-transactions/create/', intercompany.ic_transaction_create, name='ic_transaction_create'),
    path('ic-transactions/<int:pk>/', intercompany.ic_transaction_detail, name='ic_transaction_detail'),
    path('ic-transactions/<int:pk>/confirm/', intercompany.ic_transaction_confirm, name='ic_transaction_confirm'),
    path('ic-transactions/<int:pk>/post/', intercompany.ic_transaction_post, name='ic_transaction_post'),

    # === Inter-company Balances ===
    path('ic-balances/', intercompany.ic_balance_list, name='ic_balance_list'),
    path('ic-balances/<int:pk>/reconcile/', intercompany.ic_balance_reconcile, name='ic_balance_reconcile'),

    # === Currency Translation ===
    path('translation/rules/', translation.translation_rule_list, name='translation_rule_list'),
    path('translation/rules/create/', translation.translation_rule_create, name='translation_rule_create'),
    path('translation/rules/<int:pk>/edit/', translation.translation_rule_edit, name='translation_rule_edit'),
    path('translation/run/', translation.translation_run, name='translation_run'),
    path('translation/adjustments/', translation.translation_adjustment_list, name='translation_adjustment_list'),
    path('translation/adjustments/<int:pk>/', translation.translation_adjustment_detail, name='translation_adjustment_detail'),

    # === Consolidation Groups ===
    path('consolidation/groups/', consolidation.consolidation_group_list, name='consolidation_group_list'),
    path('consolidation/groups/create/', consolidation.consolidation_group_create, name='consolidation_group_create'),
    path('consolidation/groups/<int:pk>/', consolidation.consolidation_group_detail, name='consolidation_group_detail'),
    path('consolidation/groups/<int:pk>/edit/', consolidation.consolidation_group_edit, name='consolidation_group_edit'),

    # === Elimination Rules ===
    path('consolidation/rules/', consolidation.elimination_rule_list, name='elimination_rule_list'),
    path('consolidation/rules/create/', consolidation.elimination_rule_create, name='elimination_rule_create'),
    path('consolidation/rules/<int:pk>/edit/', consolidation.elimination_rule_edit, name='elimination_rule_edit'),

    # === Consolidation Runs ===
    path('consolidation/runs/', consolidation.consolidation_run_list, name='consolidation_run_list'),
    path('consolidation/runs/create/', consolidation.consolidation_run_create, name='consolidation_run_create'),
    path('consolidation/runs/<int:pk>/', consolidation.consolidation_run_detail, name='consolidation_run_detail'),
    path('consolidation/runs/<int:pk>/execute/', consolidation.consolidation_run_execute, name='consolidation_run_execute'),
    path('consolidation/runs/<int:pk>/reverse/', consolidation.consolidation_run_reverse, name='consolidation_run_reverse'),

    # === Transfer Pricing ===
    path('transfer-pricing/policies/', transfer_pricing.tp_policy_list, name='tp_policy_list'),
    path('transfer-pricing/policies/create/', transfer_pricing.tp_policy_create, name='tp_policy_create'),
    path('transfer-pricing/policies/<int:pk>/', transfer_pricing.tp_policy_detail, name='tp_policy_detail'),
    path('transfer-pricing/policies/<int:pk>/edit/', transfer_pricing.tp_policy_edit, name='tp_policy_edit'),
    path('transfer-pricing/transactions/', transfer_pricing.tp_transaction_list, name='tp_transaction_list'),
    path('transfer-pricing/transactions/create/', transfer_pricing.tp_transaction_create, name='tp_transaction_create'),
    path('transfer-pricing/transactions/<int:pk>/review/', transfer_pricing.tp_transaction_review, name='tp_transaction_review'),

    # === Regulatory Reporting ===
    path('regulatory/adjustments/', regulatory.gaap_adjustment_list, name='gaap_adjustment_list'),
    path('regulatory/adjustments/create/', regulatory.gaap_adjustment_create, name='gaap_adjustment_create'),
    path('regulatory/adjustments/<int:pk>/', regulatory.gaap_adjustment_detail, name='gaap_adjustment_detail'),
    path('regulatory/adjustments/<int:pk>/post/', regulatory.gaap_adjustment_post, name='gaap_adjustment_post'),
    path('regulatory/reports/', regulatory.regulatory_report_list, name='regulatory_report_list'),
    path('regulatory/reports/create/', regulatory.regulatory_report_create, name='regulatory_report_create'),
    path('regulatory/reports/<int:pk>/', regulatory.regulatory_report_detail, name='regulatory_report_detail'),
    path('regulatory/reports/<int:pk>/file/', regulatory.regulatory_report_file, name='regulatory_report_file'),
]
