from django import forms
from django.forms.models import inlineformset_factory
from .models import ShiftTemplate, ShiftSlotTemplate, Position
from datetime import date

# --- 1. Shift Template Creation/Editing Forms ---

class ShiftTemplateForm(forms.ModelForm):
    """
    Form for defining the core details of a standard shift template.
    """
    class Meta:
        model = ShiftTemplate
        fields = ['name', 'duration_hours', 'start_time', 'minimum_staff']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            # Note: duration_hours is left as a standard number input
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
    extra=1, # Start with one empty slot input
    can_delete=True
)

# --- 2. Shift Generation Form ---

class ShiftGenerationForm(forms.Form):
    """
    Form for the Scheduler to select a template and date range for bulk shift creation.
    """
    template = forms.ModelChoiceField(
        queryset=ShiftTemplate.objects.all().order_by('name'),
        label="Select Template to Generate"
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=date.today(),
        label="Start Date (Inclusive)"
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        # Default to 30 days from now
        initial=date.today() + forms.fields.timedelta(days=30), 
        label="End Date (Inclusive)"
    )

    def clean(self):
        cleaned_data =
