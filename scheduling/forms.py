from django import forms
from django.forms.models import inlineformset_factory
from .models import ShiftTemplate, ShiftSlotTemplate, Position, ShiftChangeRequest
from datetime import date, timedelta


# --- 1. Shift Template Creation/Editing Forms ---

class ShiftTemplateForm(forms.ModelForm):
    """
    Form for defining the core details of a standard shift template.
    """
    class Meta:
        model = ShiftTemplate
        fields = ['name', 'duration_hours', 'start_time', 'minimum_staff']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'minimum_staff': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_duration_hours(self):
        duration = self.cleaned_data.get('duration_hours')
        if duration <= 0:
            raise forms.ValidationError("Duration must be greater than zero hours.")
        return duration

    def clean_minimum_staff(self):
        staff = self.cleaned_data.get('minimum_staff')
        if staff <= 0:
            raise forms.ValidationError("Minimum staff count must be at least 1.")
        return staff


class ShiftSlotTemplateForm(forms.ModelForm):
    """
    Form for defining a single required position within a template.
    This form is used inside the formset below.
    """
    class Meta:
        model = ShiftSlotTemplate
        fields = ['position', 'count']
        widgets = {
            'position': forms.Select(attrs={'class': 'form-control'}),
            'count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure only active positions are available
        self.fields['position'].queryset = Position.objects.all().order_by('code')


# Formset factory to handle multiple ShiftSlotTemplates linked to one ShiftTemplate
# Allows the user to dynamically add/remove required positions when creating a template.
ShiftSlotTemplateFormSet = inlineformset_factory(
    ShiftTemplate, 
    ShiftSlotTemplate, 
    form=ShiftSlotTemplateForm,
    fields=('position', 'count',), 
    extra=1,  # Start with one empty slot input
    can_delete=True
)


# --- 2. Shift Generation Form ---

class ShiftGenerationForm(forms.Form):
    """
    Form for the Scheduler to select a template and date range for bulk shift creation.
    """
    template = forms.ModelChoiceField(
        queryset=ShiftTemplate.objects.all().order_by('name'),
        label="Select Template to Generate",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=date.today(),
        label="Start Date (Inclusive)"
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=lambda: date.today() + timedelta(days=30),
        label="End Date (Inclusive)"
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        
        if start and end:
            if end < start:
                raise forms.ValidationError("End date must be after start date.")
            
            # Prevent generating too many shifts at once (configurable limit)
            delta = (end - start).days
            if delta > 365:
                raise forms.ValidationError("Cannot generate more than 365 days of shifts at once.")
        
        return cleaned_data


# --- 3. Shift Change Request Form ---

class ShiftChangeRequestForm(forms.ModelForm):
    """
    Form for members to request dropping or trading a shift.
    """
    class Meta:
        model = ShiftChangeRequest
        fields = ['request_type', 'trade_with', 'reason']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-control'}),
            'trade_with': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        # Pass the user to filter eligible trade partners
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show trade_with field if request_type is TRADE
        if self.user:
            # Filter to active members only
            from django.contrib.auth.models import User
            self.fields['trade_with'].queryset = User.objects.filter(
                is_active=True
            ).exclude(pk=self.user.pk).order_by('first_name', 'last_name')
    
    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        trade_with = cleaned_data.get('trade_with')
        
        if request_type == 'TRADE' and not trade_with:
            raise forms.ValidationError("You must select a member to trade with.")
        
        if request_type == 'DROP' and trade_with:
            # Clear trade_with for drop requests
            cleaned_data['trade_with'] = None
        
        return cleaned_data


# --- 4. Shift Change Review Form (Officer Use) ---

class ShiftChangeReviewForm(forms.Form):
    """
    Simple form for officers to approve/deny shift change requests.
    """
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('deny', 'Deny'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Decision"
    )
    
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Notes (Optional)",
        help_text="Add any notes about this decision."
    )
