from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    # Member-facing views
    path('', views.TrainingDashboardView.as_view(), name='dashboard'),
    path('requirements/', views.TrainingRequirementListView.as_view(), name='requirement_list'),
    path('my-records/', views.MyTrainingRecordsView.as_view(), name='my_records'),
    path('sessions/', views.TrainingSessionListView.as_view(), name='session_list'),
    path('sessions/<int:pk>/', views.TrainingSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/register/', views.TrainingSessionRegisterView.as_view(), name='session_register'),
    
    # Officer views - Training record management
    path('records/verify/<int:pk>/', views.TrainingRecordVerifyView.as_view(), name='record_verify'),
    path('evaluations/', views.PracticalEvaluationListView.as_view(), name='evaluation_list'),
    path('evaluations/create/<int:user_id>/', views.PracticalEvaluationCreateView.as_view(), name='evaluation_create'),
    path('evaluations/<int:pk>/', views.PracticalEvaluationDetailView.as_view(), name='evaluation_detail'),
    
    # Training Officer views
    path('admin/', views.TrainingOfficerDashboardView.as_view(), name='officer_dashboard'),
    path('admin/requirements/create/', views.TrainingRequirementCreateView.as_view(), name='requirement_create'),
    path('admin/requirements/<int:pk>/edit/', views.TrainingRequirementUpdateView.as_view(), name='requirement_update'),
    path('admin/sessions/create/', views.TrainingSessionCreateView.as_view(), name='session_create'),
    path('admin/sessions/<int:pk>/edit/', views.TrainingSessionUpdateView.as_view(), name='session_update'),
    path('admin/sessions/<int:pk>/attendance/', views.TrainingSessionAttendanceView.as_view(), name='session_attendance'),
    path('admin/compliance-report/', views.ComplianceReportView.as_view(), name='compliance_report'),
    
    # API sync
    path('admin/sync-target-solutions/', views.SyncTargetSolutionsView.as_view(), name='sync_target_solutions'),
]
