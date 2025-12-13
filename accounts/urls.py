from django.urls import path
from . import views

# Set the application namespace
app_name = 'accounts'

urlpatterns = [
    # --- MEMBER DASHBOARD & PROFILE ---
    
    # Base member dashboard view (the landing page after login)
    path('dashboard/', views.MemberDashboardView.as_view(), name='member_dashboard'),
    
    # View to allow members to edit their profile information
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    
    # View to handle the upload of new or updated certification documents
    path('certifications/upload/', views.CertificationUploadView.as_view(), name='certification_upload'),


    # --- SECRETARY/VERIFICATION QUEUES (Requires IsSecretaryMixin) ---

    # Queue for viewing and processing user-submitted data changes
    path('verification/data/', views.VerificationQueueDataView.as_view(), name='verification_queue_data'),
    
    # Queue for viewing and processing user-submitted certification documents
    path('verification/documents/', views.VerificationQueueDocsView.as_view(), name='verification_queue_docs'),
    
    # Endpoint for the Secretary to approve or reject a pending data change (via POST request)
    path('verification/data/process/<int:pk>/', views.ProcessDataChangeView.as_view(), name='process_data_change'),
    
    # Endpoint for the Secretary to approve or reject a pending certification (via POST request)
    path('verification/docs/process/<int:pk>/', views.ProcessCertificationView.as_view(), name='process_certification'),
    
    # View to display a single, full document for review
    path('verification/doc/view/<int:pk>/', views.CertificationDocumentView.as_view(), name='view_certification_document'),
]
