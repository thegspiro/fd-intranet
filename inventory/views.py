# inventory/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction

from .models import InventoryItem, StockLevel, Transaction
from .forms import InventoryItemForm, StockLevelForm, TransactionForm
from fd_intranet.utils import is_quartermaster # For decorator/mixin
from accounts.models import FireDeptUser

# --- 1. Main Quartermaster Dashboard View (Protected) ---

class QuartermasterDashboardView(LoginRequiredMixin, View):
    """
    Protected dashboard for the Quartermaster role to manage inventory items,
    stock levels, and record transactions.
    """
    template_name = 'inventory/quartermaster_dashboard.html'
    
    def get(self, request):
        if not is_quartermaster(request.user):
            messages.error(request, "Access Denied. You must be the Quartermaster to view this page.")
            return redirect('dashboard')
            
        item_form = InventoryItemForm()
        stock_form = StockLevelForm()
        transaction_form = TransactionForm()
        
        inventory_summary = StockLevel.objects.select_related('item').order_by('item__name', 'location')
        recent_transactions = Transaction.objects.select_related('item', 'member').order_by('-transaction_date')[:15]
        
        context = {
            'item_form': item_form,
            'stock_form': stock_form,
            'transaction_form': transaction_form,
            'inventory_summary': inventory_summary,
            'recent_transactions': recent_transactions,
            'members': FireDeptUser.objects.all().order_by('last_name'),
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        if not is_quartermaster(request.user):
            return redirect('dashboard')
            
        # Dispatch based on which form was submitted
        if 'add_item' in request.POST:
            return self.handle_add_item(request)
        elif 'update_stock' in request.POST:
            return self.handle_update_stock(request)
        elif 'record_transaction' in request.POST:
            return self.handle_record_transaction(request)
        
        return redirect('quartermaster_dashboard')

# --- 2. Form Handlers ---

def handle_add_item(self, request):
    item_form = InventoryItemForm(request.POST)
    if item_form.is_valid():
        item_form.save()
        messages.success(request, f"New inventory item '{item_form.cleaned_data['name']}' added.")
    else:
        messages.error(request, "Error adding item.")
    return redirect('quartermaster_dashboard')

def handle_update_stock(self, request):
    # This logic should be used for initial setup or bulk inventory counting
    stock_form = StockLevelForm(request.POST)
    if stock_form.is_valid():
        stock_form.save()
        messages.success(request, "Stock level updated.")
    else:
        messages.error(request, "Error updating stock.")
    return redirect('quartermaster_dashboard')

def handle_record_transaction(self, request):
    transaction_form = TransactionForm(request.POST)
    if transaction_form.is_valid():
        trans = transaction_form.save(commit=False)
        trans.recorded_by = request.user
        
        item = trans.item
        quantity = trans.quantity
        trans_type = trans.transaction_type
        
        # 1. Update Stock Level (Simplified: using a default location)
        # This is CRITICAL: Ensure stock levels are adjusted accurately
        try:
            stock, created = StockLevel.objects.get_or_create(
                item=item, 
                location='Main Station Stock', # Simplified default location
                defaults={'current_quantity': 0}
            )
            
            if trans_type == 'ASSIGNMENT' or trans_type == 'SALE' or trans_type == 'RETIREMENT':
                if stock.current_quantity < quantity:
                    messages.error(request, f"Cannot complete transaction: Only {stock.current_quantity} of {item.name} in stock.")
                    return redirect('quartermaster_dashboard')
                stock.current_quantity -= quantity
                
            elif trans_type == 'RETURN':
                stock.current_quantity += quantity
                
            stock.save()
            
            # 2. Save Transaction Record
            trans.save()
            messages.success(request, f"Transaction recorded: {trans_type} of {quantity} x {item.name}.")

        except Exception as e:
            messages.error(request, f"Critical Transaction Error: {e}")
            
    else:
        messages.error(request, f"Transaction form error: {transaction_form.errors.as_text()}")
        
    return redirect('quartermaster_dashboard')

# --- 3. Individual Member History View ---

class MemberInventoryHistoryView(LoginRequiredMixin, View):
    """Shows all items currently assigned to a specific member."""
    template_name = 'inventory/member_history.html'

    def get(self, request, pk):
        member = get_object_or_404(FireDeptUser, pk=pk)
        
        # Find all un-returned assignment transactions for this member
        assigned_items = Transaction.objects.filter(
            member=member,
            transaction_type='ASSIGNMENT'
            # NOTE: True history requires tracking returns properly (e.g., using a separate 'Return' flag)
        ).select_related('item').order_by('-transaction_date')

        context = {
            'target_member': member,
            'assigned_items': assigned_items
        }
        return render(request, self.template_name, context)
