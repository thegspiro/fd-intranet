"""
Compliance Module URL Configuration
"""
from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    # Member-facing views
    path('', views.MemberComplianceDashboard.as_view(), name='dashboard'),
    
    # Compliance Officer views
    path('officer/', views.ComplianceOfficerDashboard.as_view(), name='officer_dashboard'),
    path('officer/member/<int:pk>/', views.MemberComplianceDetail.as_view(), name='member_detail'),
    path('officer/add-physical/', views.AddMedicalPhysical.as_view(), name='add_physical'),
    path('officer/add-fit-test/', views.AddFitTest.as_view(), name='add_fit_test'),
    path('officer/add-immunization/', views.AddImmunization.as_view(), name='add_immunization'),
    
    # OSHA logs
    path('osha/', views.OSHALogList.as_view(), name='osha_logs'),
    path('osha/add/', views.AddOSHALog.as_view(), name='add_osha_log'),
    
    # Exposure incidents
    path('exposure/add/', views.AddExposureIncident.as_view(), name='add_exposure'),
    
    # Reports
    path('reports/', views.ComplianceReports.as_view(), name='reports'),
]
