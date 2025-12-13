from django.urls import path
from . import views

# Set the application namespace
app_name = 'inventory'

urlpatterns = [
    # --- 1. MEMBER-FACING SUPPLY REQUESTS ---
    
    # Form to submit a new supply request
    path('request/submit/', views.SupplyRequestCreateView.as_view(), name='request_submit'),
    
    # List of the user's past and pending supply requests
    path('request/list/', views.SupplyRequestListView.as_view(), name='request_list'),


    # --- 2. QUARTERMASTER DASHBOARD & QUEUE ---

    # Quartermaster Dashboard (Landing page)
    path('qm/', views.QuartermasterDashboardView.as_view(), name='quartermaster_dashboard'),
    
    # Quartermaster Queue for reviewing and processing all pending requests
    path('qm/requests/', views.SupplyRequestQueueView.as_view(), name='request_queue'),
    
    # View to process a specific request (update status, add notes)
    path('qm/requests/process/<int:pk>/', views.SupplyRequestProcessView.as_view(), name='request_process'),


    # --- 3. ASSET MANAGEMENT ---

    # List of all trackable assets
    path('qm/assets/', views.AssetListView.as_view(), name='asset_list'),
    
    # Create a new asset record
    path('qm/assets/create/', views.AssetCreateUpdateView.as_view(), name='asset_create'),
    
    # View asset details and maintenance history
    path('qm/assets/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    
    # Edit an existing asset record
    path('qm/assets/edit/<int:pk>/', views.AssetCreateUpdateView.as_view(), name='asset_edit'),

    # --- 4. MAINTENANCE LOGS ---

    # Endpoint to create a new maintenance log for an asset (via POST from detail view)
    path('qm/maintenance/create/', views.MaintenanceLogCreateView.as_view(), name='maintenance_log_create'),


    # --- 5. CATEGORY MANAGEMENT ---
    
    # List of all inventory categories
    path('qm/categories/', views.CategoryListView.as_view(), name='category_list'),

    # Create/Edit inventory categories
    path('qm/categories/form/', views.CategoryCreateUpdateView.as_view(), name='category_create'),
    path('qm/categories/form/<int:pk>/', views.CategoryCreateUpdateView.as_view(), name='category_edit'),
]
