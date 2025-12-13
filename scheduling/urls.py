from django.urls import path
from . import views

# Set the application namespace
app_name = 'scheduling'

urlpatterns = [
    # --- MEMBER-FACING VIEWS ---
    
    # The main calendar view for all members to see available shifts
    path('', views.ShiftCalendarView.as_view(), name='shift_calendar'),
    
    # Endpoint to sign up for a specific shift slot (via POST request)
    path('signup/<int:pk>/', views.ShiftSignupView.as_view(), name='shift_signup'),
    
    # Endpoint to drop a shift slot (via POST request)
    path('drop/<int:pk>/', views.ShiftDropView.as_view(), name='shift_drop'),
    
    # Endpoint to download the user's scheduled shifts in iCalendar format
    path('export/ical/', views.ICalExportView.as_view(), name='ical_export'),


    # --- SCHEDULER-FACING ADMINISTRATIVE VIEWS (Requires IsSchedulerMixin) ---

    # Scheduler Dashboard: Landing page for all admin tools (generation form, templates list)
    path('admin/dashboard/', views.SchedulerDashboardView.as_view(), name='scheduler_dashboard'),
    
    # View to create a new ShiftTemplate (including its required positions/slots)
    path('admin/template/create/', views.ShiftTemplateCreateView.as_view(), name='template_create'),
    
    # Endpoint to handle the bulk generation of Shifts based on a date range and template (via POST request)
    path('admin/generate/', views.ShiftGeneratorView.as_view(), name='shift_generator'),
]
