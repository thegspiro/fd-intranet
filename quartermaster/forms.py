"""
Quartermaster Module Forms
"""
from django import forms
from django.contrib.auth.models import User
from .models import (
    GearItem, GearInspection, GearRequest,
    GearAssignment, InventoryAudit
)


class GearItemForm(forms.ModelForm):
    """Form for adding/editing gear items"""
    
    class Meta:
        model = GearItem
        fields = [
            'item_number', 'category', 'manufacturer', 'model_number',
            'size', 'purchase_date', 'purchase_price', 'vendor',
            'manufacture_date', 'condition', 'current_location', 'photo', 'notes'
        ]
        widgets = {
            'item_number': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vendor': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacture_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'current_location': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class GearInspectionForm(forms.ModelForm):
    """Form for gear inspections"""
    
    class Meta:
        model = GearInspection
        fields = [
            'gear_item', 'result', 'findings',
            'deficiencies', 'action_taken', 'photo'
        ]
        widgets = {
            'gear_item': forms.Select(attrs={'class': 'form-control'}),
            'result': forms.Select(attrs={'class': 'form-control'}),
            'findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe inspection findings...'
            }),
            'deficiencies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List any deficiencies found...'
            }),
            'action_taken': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe corrective action taken...'
            }),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class GearRequestForm(forms.ModelForm):
    """Form for requesting gear"""
    
    class Meta:
        model = GearRequest
        fields = [
            'category', 'item_description', 'size_needed',
            'is_urgent', 'justification'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'item_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the gear you need...'
            }),
            'size_needed': forms.TextInput(attrs={'class': 'form-control'}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain why you need this gear...'
            }),
        }


class GearAssignmentForm(forms.ModelForm):
    """Form for assigning gear"""
    
    class Meta:
        model = GearAssignment
        fields = [
            'gear_item', 'assigned_to', 'condition_at_issue', 'notes'
        ]
        widgets = {
            'gear_item': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'condition_at_issue': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available gear
        self.fields['gear_item'].queryset = GearItem.objects.filter(
            is_available=True,
            condition__in=['NEW', 'GOOD', 'FAIR']
        )
        # Only show active members
        self.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')


class InventoryAuditForm(forms.ModelForm):
    """Form for inventory audits"""
    
    class Meta:
        model = InventoryAudit
        fields = [
            'category', 'items_counted', 'discrepancies_found',
            'is_complete', 'notes'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'items_counted': forms.NumberInput(attrs={'class': 'form-control'}),
            'discrepancies_found': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_complete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Audit notes and discrepancy details...'
            }),
        }
