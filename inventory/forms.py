# inventory/forms.py

from django import forms
from .models import InventoryItem, StockLevel, Transaction
from accounts.models import FireDeptUser

# --- 1. Base Item Creation Form ---

class InventoryItemForm(forms.ModelForm):
    """Form to define a new type of inventory item."""
    class Meta:
        model = InventoryItem
        fields = '__all__'

# --- 2. Stock Level Update Form ---

class StockLevelForm(forms.ModelForm):
    """Form to manage stock levels at a specific location."""
    class Meta:
        model = StockLevel
        fields = ['item', 'location', 'current_quantity']
        
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'Main Station Stock, Truck 1'}),
            'current_quantity': forms.NumberInput(attrs={'min': 0}),
        }

# --- 3. Transaction Recording Form (Assignment/Sale/Return) ---

class TransactionForm(forms.ModelForm):
    """
    Form used by the Quartermaster to record movements of inventory.
    The view will handle filtering the member based on the transaction type.
    """
    # Override fields to make member selection easier and more specific
    member = forms.ModelChoiceField(
        queryset=FireDeptUser.objects.all().order_by('last_name'),
        label="Member",
        required=True,
        help_text="The member receiving or returning the item."
    )
    
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'item', 'member', 'quantity', 'serial_number']
        
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'placeholder': 'Optional if not serialized'}),
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        serial_number = cleaned_data.get('serial_number')

        # Logic: If item is serial tracked, serial_number must be provided
        if item and item.serial_tracked and not serial_number:
            raise forms.ValidationError(
                "This item is serial-tracked. A unique serial number is required."
            )
        
        # Further validation (e.g., checking if enough stock exists) should be done in the view's post method.
        return cleaned_data
