from django import forms
from django.contrib.auth.models import User
from .models import Asset, Category, MaintenanceLog, SupplyRequest, ASSET_STATUS_CHOICES
from datetime import date

# --- 1. Category Form (Admin/Quartermaster) ---

class CategoryForm(forms.ModelForm):
    """
    Form for creating or updating inventory categories.
    """
    class Meta:
        model = Category
        fields = ['name', 'description']


# --- 2. Asset Form (Quartermaster) ---

class AssetForm(forms.ModelForm):
    """
    Form for creating or updating a single trackable asset.
    """
    class Meta:
        model = Asset
        fields = [
            'category', 'name', 'serial_number', 'asset_tag', 
            'location', 'status', 'purchase_date', 'purchase_cost',
            'last_inspection_date', 'next_inspection_date'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'last_inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'next_inspection_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure categories are ordered
        self.fields['category'].queryset = Category.objects.all().order_by('name')


# --- 3. Maintenance Log Form (Quartermaster) ---

class MaintenanceLogForm(forms.ModelForm):
    """
    Form for logging maintenance or repair activity on an asset.
    """
    class Meta:
        model = MaintenanceLog
        fields = ['asset', 'date_of_service', 'description', 'cost', 'new_next_inspection_date']
        widgets = {
            'date_of_service': forms.DateInput(attrs={'type': 'date'}),
            'new_next_inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'asset': forms.HiddenInput(), # Asset is typically passed from the detail view
        }
        
    def clean(self):
        cleaned_data = super().clean()
        date_of_service = cleaned_data.get('date_of_service')
        
        if date_of_service and date_of_service > date.today():
            raise forms.ValidationError("Date of service cannot be in the future.")
            
        return cleaned_data


# --- 4. Member Supply Request Form ---

class SupplyRequestForm(forms.ModelForm):
    """
    Form for a standard member to submit a request for supplies.
    (Status and processing fields are omitted.)
    """
    class Meta:
        model = SupplyRequest
        fields = ['item_description', 'quantity', 'justification']


# --- 5. Quartermaster Supply Request Processing Form ---

class SupplyRequestProcessForm(forms.ModelForm):
    """
    Form used by the Quartermaster to change the status of a request and add notes.
    """
    class Meta:
        model = SupplyRequest
        # Only allow Quartermaster to change status and add internal notes
        fields = ['status', 'quartermaster_notes']
