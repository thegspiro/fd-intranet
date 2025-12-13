from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, MemberCertification, CertificationStandard

# --- 1. Profile Editing Form ---

class ProfileEditForm(forms.ModelForm):
    """
    Form for members to submit updates to their core profile data.
    Note: Changes are submitted to the DataChangeRequest queue, 
    NOT saved directly by this form's save() method.
    """
    
    # Fields from the User model (FirstName, LastName, Email)
    first_name = forms.CharField(max_length=150, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")

    class Meta:
        model = UserProfile
        fields = ['badge_number', 'phone_number', 'date_of_birth']
        widgets = {
            # Use HTML5 date input for better user experience
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If an instance exists (which it should for an UpdateView)
        if self.instance and self.instance.user:
            # Populate the User fields that are being displayed in this form
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    # We override save() in the view (accounts/views.py) to send data to the queue,
    # rather than saving directly to the models.
    def save(self, commit=True):
        # Prevent direct saving here; the view handles creating the DataChangeRequest
        return self.instance 

# --- 2. Certification Upload Form ---

class CertificationUploadForm(forms.ModelForm):
    """
    Form for members to upload a new certification document.
    """
    class Meta:
        model = MemberCertification
        fields = ['standard', 'issue_date', 'expiration_date', 'document']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }
