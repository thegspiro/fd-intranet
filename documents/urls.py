from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Main document library
    path('', views.DocumentLibraryView.as_view(), name='library'),
    path('search/', views.DocumentSearchView.as_view(), name='search'),
    path('category/<int:pk>/', views.DocumentCategoryView.as_view(), name='category'),
    
    # Document viewing
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/view/', views.DocumentViewerView.as_view(), name='viewer'),
    path('<int:pk>/download/', views.DocumentDownloadView.as_view(), name='download'),
    path('<int:pk>/acknowledge/', views.DocumentAcknowledgeView.as_view(), name='acknowledge'),
    
    # Document management
    path('create/', views.DocumentCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='update'),
    path('<int:pk>/new-version/', views.DocumentNewVersionView.as_view(), name='new_version'),
    path('<int:pk>/archive/', views.DocumentArchiveView.as_view(), name='archive'),
    path('<int:pk>/history/', views.DocumentHistoryView.as_view(), name='history'),
    
    # Categories management
    path('admin/categories/', views.CategoryManagementView.as_view(), name='category_management'),
    path('admin/categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('admin/categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # Document requests
    path('requests/', views.DocumentRequestListView.as_view(), name='request_list'),
    path('requests/create/', views.DocumentRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', views.DocumentRequestDetailView.as_view(), name='request_detail'),
    path('admin/requests/', views.DocumentRequestManagementView.as_view(), name='request_management'),
    path('admin/requests/<int:pk>/review/', views.DocumentRequestReviewView.as_view(), name='request_review'),
    
    # Reports and analytics
    path('admin/analytics/', views.DocumentAnalyticsView.as_view(), name='analytics'),
    path('admin/review-schedule/', views.DocumentReviewScheduleView.as_view(), name='review_schedule'),
    path('admin/acknowledgments/', views.AcknowledgmentReportView.as_view(), name='acknowledgment_report'),
]
