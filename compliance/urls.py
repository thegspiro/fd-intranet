from django.urls import path
from . import views

# Set the application namespace
app_name = 'compliance'

urlpatterns = [
    # --- 1. DASHBOARD & CHECKS ---

    # Main Compliance Officer Dashboard
    path('', views.ComplianceDashboardView.as_view(), name='compliance_dashboard'),

    # Administrative endpoint to manually run the full compliance audit
    path('run-check/', views.RunSafetyCheckView.as_view(), name='run_safety_check'),


    # --- 2. SAFETY STANDARDS MANAGEMENT ---

    # List of all defined Safety Standards
    path('standards/', views.SafetyStandardListView.as_view(), name='safety_standard_list'),
    
    # Create a new Safety Standard
    path('standards/create/', views.SafetyStandardCreateUpdateView.as_view(), name='safety_standard_create'),
    
    # Edit an existing Safety Standard
    path('standards/edit/<int:pk>/', views.SafetyStandardCreateUpdateView.as_view(), name='safety_standard_edit'),


    # --- 3. MEMBER RECORDS MANAGEMENT ---

    # Create a new compliance record for a specific member/standard
    path('records/create/', views.MemberRecordCreateView.as_view(), name='member_record_create'),
    
    # Note: We can add an edit/list view for records later, but the create view is the core function.


    # --- 4. SAFETY NET CONFIGURATION ---

    # List of all defined Safety Net configurations
    path('safety-nets/', views.SafetyNetListView.as_view(), name='safety_net_list'),
    
    # Create a new Safety Net Configuration
    path('safety-nets/create/', views.SafetyNetCreateUpdateView.as_view(), name='safety_net_create'),
    
    # Edit an existing Safety Net Configuration
    path('safety-nets/edit/<int:pk>/', views.SafetyNetCreateUpdateView.as_view(), name='safety_net_edit'),
]
