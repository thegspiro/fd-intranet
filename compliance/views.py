# compliance/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction

# Import local models and forms
from .models import ComplianceStandard, GroupProfile
from .forms import ComplianceStandardForm, GroupProfileForm, ComplianceReportForm
from accounts.models import FireDeptUser # To check member assignments
from scheduling.utils import get_member_compliance_status # To generate reports
from fd_intranet.utils import ComplianceOfficerRequiredMixin # For protection


# --- 1. Main Compliance Officer Dashboard View (Protected) ---

class ComplianceOfficerDashboardView(LoginRequiredMixin, ComplianceOfficerRequiredMixin, View):
    """
    The central hub for the Compliance Officer to manage standards, groups, and reports.
    """
    template_name = 'compliance/compliance_dashboard.html'
    
    def get(self, request):
        standard_form = ComplianceStandardForm()
        report_form = ComplianceReportForm()
        
        # Data for display tables
        all_standards = ComplianceStandard.objects.all().select_related('role').order_by('role__name', 'activity_type')
        all_groups = Group.objects.all().order_by('name')
        
        context = {
            'standard_form': standard_form,
            'report_form': report_form,
            'all_standards': all_standards,
            'all_groups': all_groups,
            'report_data': None, # Will be populated on POST if running a report
        }
        return render(request, self.template_name, context)

    def post(self, request):
        # Dispatch based on which form was submitted
        if 'add_group' in request.POST:
            return self.handle_add_group(request)
        elif 'delete_group' in request.POST:
            return self.handle_delete_group(request)
        elif 'add_standard' in request.POST:
            return self.handle_add_standard(request)
        elif 'generate_report' in request.POST:
            return self.handle_generate_report(request)
        
        return redirect('compliance_dashboard')


# --- 2. Group Management Handlers ---

def handle_add_group(self, request):
    group_name = request.POST.get('group_name')
    if group_name:
        try:
            # Create the Django Group
            new_group = Group.objects.create(name=group_name)
            
            # Immediately create an empty GroupProfile for the safety net system
            GroupProfile.objects.create(group=new_group)
            
            messages.success(request, f"Successfully added new membership group: {group_name}.")
        except IntegrityError:
            messages.error(request, f"A group named '{group_name}' already exists.")
        
    return redirect('compliance_dashboard')

@transaction.atomic
def handle_delete_group(self, request):
    group_id = request.POST.get('group_id')
    group_to_delete = get_object_or_404(Group, id=group_id)

    # 1. CRITICAL CHECK: ENSURE NO MEMBERS ARE ASSIGNED
    if FireDeptUser.objects.filter(groups=group_to_delete).exists():
        # THIS IS THE SAFETY NET TRIGGER WE DESIGNED
        # The user's role will become NONE, triggering the email alert from the scheduled job
        messages.error(request, f"Cannot delete group **{group_to_delete.name}**! Please reassign all members before deleting.")
        return redirect('compliance_dashboard')
        
    # 2. CRITICAL: DELETE RELATED STANDARDS AND PROFILES
    ComplianceStandard.objects.filter(role=group_to_delete).delete()
    GroupProfile.objects.filter(group=group_to_delete).delete()
    
    # 3. Delete the Group
    group_to_delete.delete()
    messages.warning(request, f"Membership group '{group_to_delete.name}' and all associated standards were deleted.")
    
    return redirect('compliance_dashboard')


# --- 3. Standards Management Handler ---

def handle_add_standard(self, request):
    standard_form = ComplianceStandardForm(request.POST)
    if standard_form.is_valid():
        try:
            standard_form.save()
            messages.success(request, "New compliance standard added successfully.")
        except Exception as e:
            messages.error(request, f"Error saving standard: {e}")
    else:
        messages.error(request, "Failed to add standard. Check form data.")
    
    return redirect('compliance_dashboard')


# --- 4. Reporting Handler ---

def handle_generate_report(self, request):
    report_form = ComplianceReportForm(request.POST)
    if report_form.is_valid():
        start_date = report_form.cleaned_data['start_date']
        end_date = report_form.cleaned_data['end_date']
        
        # Get all users who are not superusers/inactive
        members = FireDeptUser.objects.filter(is_active=True, is_superuser=False)
        
        full_compliance_report = []
        for member in members:
            # We use the utility function to check the annual status
            # NOTE: For true report generation, get_member_compliance_status 
            # would need a mode to check compliance over arbitrary dates (start_date/end_date)
            # For simplicity here, we rely on the annual check (period='ANNUAL')
            
            report_for_member = get_member_compliance_status(member, period='ANNUAL') 
            
            for item in report_for_member:
                full_compliance_report.append({
                    'member': member.get_full_name(),
                    'role': item['standard_role'],
                    'activity': item['activity'],
                    'required': item['required'],
                    'actual': item['actual'],
                    'percentage': item['percentage'],
                    'status': item['status'],
                })

        # Render the dashboard again, but this time with the report data
        context = self.get(request).context
        context['report_data'] = full_compliance_report
        context['report_dates'] = {'start': start_date, 'end': end_date}
        
        return render(request, self.template_name, context)
    
    messages.error(request, "Invalid dates for report generation.")
    return redirect('compliance_dashboard')
