from django.urls import path

from . import views

app_name = 'fixed_assets'

urlpatterns = [
    # Asset Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),

    # Asset Locations
    path('locations/', views.location_list, name='location_list'),
    path('locations/create/', views.location_create, name='location_create'),
    path('locations/<int:pk>/edit/', views.location_edit, name='location_edit'),

    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/create/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/edit/', views.asset_edit, name='asset_edit'),

    # Acquisitions
    path('acquisitions/', views.acquisition_list, name='acquisition_list'),
    path('acquisitions/create/', views.acquisition_create, name='acquisition_create'),
    path('acquisitions/<int:pk>/capitalize/', views.acquisition_capitalize, name='acquisition_capitalize'),

    # Depreciation
    path('depreciation/', views.depreciation_dashboard, name='depreciation_dashboard'),
    path('depreciation/run/', views.run_depreciation, name='run_depreciation'),
    path('depreciation/schedule/<int:pk>/', views.schedule_detail, name='schedule_detail'),

    # Transfers
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/create/', views.transfer_create, name='transfer_create'),
    path('transfers/<int:pk>/approve/', views.transfer_approve, name='transfer_approve'),
    path('transfers/<int:pk>/complete/', views.transfer_complete, name='transfer_complete'),

    # Disposals
    path('disposals/', views.disposal_list, name='disposal_list'),
    path('disposals/create/', views.disposal_create, name='disposal_create'),
    path('disposals/<int:pk>/process/', views.disposal_process, name='disposal_process'),

    # Impairment
    path('impairment/', views.impairment_list, name='impairment_list'),
    path('impairment/create/', views.impairment_create, name='impairment_create'),

    # Physical Inventory
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/create/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/count/', views.inventory_count, name='inventory_count'),
    path('inventory/<int:pk>/reconcile/', views.inventory_reconcile, name='inventory_reconcile'),

    # Tax Depreciation
    path('tax-books/', views.tax_book_list, name='tax_book_list'),
    path('tax-books/create/', views.tax_book_create, name='tax_book_create'),
    path('tax-books/<int:pk>/', views.tax_book_detail, name='tax_book_detail'),
    path('tax-entries/create/', views.tax_entry_create, name='tax_entry_create'),
]
