from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone

from fd_intranet.utils import IsQuartermasterMixin
from .models import Asset, Category, MaintenanceLog, SupplyRequest
from .forms import AssetForm, CategoryForm, MaintenanceLogForm, SupplyRequestForm, SupplyRequestProcessForm

# --- 1. MEMBER-FACING VIEWS ---

class SupplyRequestCreateView(LoginRequiredMixin, CreateView):
    """
    Allows any logged-in member to submit a request for supplies.
    """
    model = SupplyRequest
    form_class = SupplyRequestForm
    template_name = 'inventory/supply_request_form.html'
    success_url = reverse_lazy('inventory:request_list')

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        messages.success(self.request, "Your supply request has been submitted to the Quartermaster.")
        return super().form_valid(form)

class SupplyRequestListView(LoginRequiredMixin, ListView):
    """
    Displays a list of the current user's past and pending supply requests.
    """
    model = SupplyRequest
    template_name = 'inventory/supply_request_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        # Members only see their own requests
        return SupplyRequest.objects.filter(requested_by=self.request.user).order_by('-request_date')

# --- 2. QUARTERMASTER-FACING VIEWS ---

class QuartermasterDashboardView(IsQuartermasterMixin, TemplateView):
    """
    Main landing page for the Quartermaster. Provides an overview of pending requests
    and critical asset status.
    """
    template_name = 'inventory/quartermaster_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pending Requests Overview
        context['pending_requests'] = SupplyRequest.objects.filter(status='PENDING').order_by('-request_date')[:10]
        context['pending_count'] = SupplyRequest.objects.filter(status='PENDING').count()
        
        # Critical Asset Status
        context['out_of_service_count'] = Asset.objects.filter(status='OUT').count()
        
        # Upcoming Inspections (Next 30 days)
        thirty_days = timezone.now().date() + timedelta(days=30)
        context['upcoming_inspections'] = Asset.objects.filter(
            next_inspection_date__lte=thirty_days,
            status='SERVICE'
        ).order_by('next_inspection_date')[:10]
        
        return context


# --- 3. ASSET MANAGEMENT ---

class AssetListView(IsQuartermasterMixin, ListView):
    """Lists all assets with filtering and sorting capabilities."""
    model = Asset
    template_name = 'inventory/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 25

    def get
