from django import forms
from .models import SafetyStandard, MemberComplianceRecord, SafetyNetConfiguration, SAFETY_NET_TYPE_CHOICES
from accounts.models import CertificationStandard
from scheduling.models import Position
from django.contrib.auth.models import User

# --- 1. SafetyStandard Definition Form ---

class SafetyStandardForm(forms.ModelForm):
    """
    Form for creating or updating department-wide Safety Standards.
    """
    class Meta:
        model = SafetyStandard
        fields = ['name', 'description', 'is_mandatory_annual', 'linked_certification']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter certification choices to show only active standards
        self.fields['linked_certification'].queryset = CertificationStandard.objects.all().order_by('name')


# --- 2. MemberComplianceRecord Management Form ---

class MemberComplianceRecordForm(forms.ModelForm):
    """
    Form for the Compliance Officer to record a member's compliance status
    against a specific safety standard.
    """
    class Meta:
        model = MemberComplianceRecord
        fields = ['user', 'standard', 'is_compliant', 'date_met', 'notes']
        widgets = {
            'date_met': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users and standards
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('last_name')
        self.fields['standard'].queryset = SafetyStandard.objects.all().order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        standard = cleaned_data.get('standard')
        
        # Ensure only one active record exists per user/standard (enforced by model unique_together)
        # We can add custom validation here if needed, but the model constraint handles the hard stop.

        return cleaned_data

# --- 3. SafetyNetConfiguration Form ---

class SafetyNetConfigurationForm(forms.ModelForm):
    """
    Form for defining custom safety net rules (manpower minimums, qualification overrides).
    Uses JavaScript to dynamically show/hide the 'position' field based on the 'type'.
    """
    class Meta:
        model = SafetyNetConfiguration
        fields = ['name', 'type', 'position', 'enforcement_value', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate position choices
        self.fields['position'].queryset = Position.objects.all().order_by('code')
        
        # Add a custom attribute to the type field for JavaScript targeting
        self.fields['type'].widget.attrs.update({'id': 'id_safety_net_type', 'class': 'form-control'})
        
        # Add Bootstrap styling
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
