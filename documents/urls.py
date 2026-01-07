"""
Documents Module URL Configuration
"""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Public/Member views
    path('', views.DocumentLibrary.as_view(), name='library'),
    path('<int:pk>/', views.DocumentDetail.as_view(), name='document_detail'),
    path('<int:pk>/viewer/', views.DocumentViewer.as_view(), name='viewer'),
    path('<int:pk>/download/', views.DocumentDownload.as_view(), name='download'),
    path('<int:pk>/acknowledge/', views.AcknowledgeDocument.as_view(), name='acknowledge'),
    
    # Document requests
    path('request/', views.RequestDocument.as_view(), name='request_document'),
    path('my-requests/', views.MyDocumentRequests.as_view(), name='my_requests'),
    
    # Document management
    path('management/', views.DocumentManagementDashboard.as_view(), name='management_dashboard'),
    path('management/create/', views.CreateDocument.as_view(), name='create_document'),
    path('management/<int:pk>/edit/', views.EditDocument.as_view(), name='edit_document'),
    path('management/<int:pk>/new-version/', views.CreateNewVersion.as_view(), name='new_version'),
    path('management/<int:pk>/approve/', views.ApproveDocument.as_view(), name='approve_document'),
    path('management/<int:pk>/archive/', views.ArchiveDocument.as_view(), name='archive_document'),
    path('management/request/<int:pk>/', views.ProcessDocumentRequest.as_view(), name='process_request'),
    
    # Category management
    path('management/categories/', views.CategoryManagement.as_view(), name='category_management'),
    path('management/categories/create/', views.CreateCategory.as_view(), name='create_category'),
    path('management/categories/<int:pk>/edit/', views.EditCategory.as_view(), name='edit_category'),
    
    # Reports
    path('reports/analytics/', views.DocumentAnalytics.as_view(), name='analytics'),
    path('reports/<int:pk>/acknowledgments/', views.AcknowledgmentReport.as_view(), name='acknowledgment_report'),
]
