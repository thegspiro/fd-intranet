# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group
from .models import FireDeptUser, Certification, PersonnelRecord

# --- 1. Member Profile Update Form ---

class MemberProfileForm(forms.ModelForm):
    """
    Form for members to submit changes to their own profile information.
    Note: The view (MemberProfileUpdateView) handles saving this data to PendingChange.
    """
    class Meta:
        model = FireDeptUser
        # These are the fields the member can initiate changes for.
        fields = [
            'first_name', 'last_name', 'address', 'city', 'state', 
            'zip_code', 'phone_number', 'email'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'user@example.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'XXX-XXX-XXXX'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevent the user from changing their username via this form
        if 'username' in self.fields:
            self.fields['username'].disabled = True

# --- 2. Certification/Document Upload Form ---

class CertificationUploadForm(forms.ModelForm):
    """
    Form for members to upload a document (e.g., CPR card) and set its expiration.
    """
    certification = forms.ModelChoiceField(
        queryset=Certification.objects.all(),
        label="Certification Type",
        help_text="Select the type of document you are uploading (e.g., EMT, CPR)."
    )
    
    class Meta:
        model = PersonnelRecord
        # The member only provides the file and expiration date
        fields = ['certification', 'attachment_file', 'document_expiration']
        widgets = {
            'document_expiration': forms.DateInput(attrs={'type': 'date'}),
            'attachment_file': forms.FileInput(attrs={'accept': '.pdf,.jpg,.png'})
        }

    # Custom validation could be added here to ensure the file is not too large or is a valid type.

# --- 3. Administrative Role Assignment Form ---

class RoleAssignmentAdminForm(forms.Form):
    """
    Form used by authorized leadership (Chief, President, etc.) to change a member's roles.
    Note: This is an un-bound form used to process the POST request in RoleAssignmentView.
    """
    member = forms.ModelChoiceField(
        queryset=FireDeptUser.objects.all().order_by('last_name'),
        label="Select Member",
        required=True
    )
    
    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        label="Assigned Roles",
        required=False,
        help_text="Select all groups/roles this member should belong to."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We might dynamically update the member's current roles here if bound to an instance
        pass
