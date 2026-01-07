"""
Archives Module Views
Handles historical records, legacy data, and department history
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta, date
from .models import (
    HistoricalShiftRecord, LegacyMemberData, IncidentArchive,
    AnnualReport, EquipmentHistory
)
from .forms import (
    HistoricalShiftRecordForm, LegacyMemberDataForm,
    IncidentArchiveForm, AnnualReportForm, EquipmentHistoryForm
)


class IsArchivistMixin(UserPassesTestMixin):
    """Mixin to restrict access to Chief Officers and designated archivists"""
    def test_func(self):
        return self.request.user.groups.filter(
            name__in=['Chief Officers', 'Secretary']
        ).exists()


# Public/Member Views

class ArchivesDashboard(LoginRequiredMixin, ListView):
    """Main archives dashboard"""
    template_name = 'archives/dashboard.html'
    context_object_name = 'recent_incidents'
    
    def get_queryset(self):
        return IncidentArchive.objects.all().order_by('-incident_date')[:10]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        current_year = timezone.now().year
        
        context.update({
            'total_incidents': IncidentArchive.objects.count(),
            'total_shifts': HistoricalShiftRecord.objects.count(),
            'total_legacy_members': LegacyMemberData.objects.count(),
            'annual_reports': AnnualReport.objects.all().order_by('-year')[:5],
            'incidents_ytd': IncidentArchive.objects.filter(
                incident_date__year=current_year
            ).count(),
            'equipment_count': EquipmentHistory.objects.count(),
        })
        
        return context


class HistoricalShiftList(LoginRequiredMixin, ListView):
    """List historical shift records"""
    model = HistoricalShiftRecord
    template_name = 'archives/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = HistoricalShiftRecord.objects.all()
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(shift_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(shift_date__lte=end_date)
        
        # Filter by template
        template = self.request.GET.get('template')
        if template:
            queryset = queryset.filter(shift_template_name__icontains=template)
        
        # Filter by OIC
        oic = self.request.GET.get('oic')
        if oic:
            queryset = queryset.filter(officer_in_charge__icontains=oic)
        
        return queryset.order_by('-shift_date')


class HistoricalShiftDetail(LoginRequiredMixin, DetailView):
    """Detail view of historical shift"""
    model = HistoricalShiftRecord
    template_name = 'archives/shift_detail.html'
    context_object_name = 'shift'


class OnThisDay(LoginRequiredMixin, ListView):
    """Show historical events from this day in history"""
    template_name = 'archives/on_this_day.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        today = timezone.now().date()
        
        # Get events from this day in previous years
        incidents = IncidentArchive.objects.filter(
            incident_date__month=today.month,
            incident_date__day=today.day
        ).exclude(
            incident_date__year=today.year
        ).order_by('-incident_date')
        
        return incidents
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Get shifts from this day
        context['historical_shifts'] = HistoricalShiftRecord.objects.filter(
            shift_date__month=today.month,
            shift_date__day=today.day
        ).exclude(
            shift_date__year=today.year
        ).order_by('-shift_date')
        
        context['today'] = today
        
        return context


class LegacyMemberList(LoginRequiredMixin, ListView):
    """List legacy/retired members"""
    model = LegacyMemberData
    template_name = 'archives/legacy_members.html'
    context_object_name = 'members'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = LegacyMemberData.objects.all()
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(badge_number__icontains=search)
            )
        
        # Filter by separation type
        sep_type = self.request.GET.get('separation_type')
        if sep_type:
            queryset = queryset.filter(separation_type=sep_type)
        
        return queryset.order_by('-separation_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['separation_types'] = LegacyMemberData.SEPARATION_TYPES
        return context


class LegacyMemberDetail(LoginRequiredMixin, DetailView):
    """Detail view of legacy member"""
    model = LegacyMemberData
    template_name = 'archives/legacy_member_detail.html'
    context_object_name = 'member'


class IncidentArchiveList(LoginRequiredMixin, ListView):
    """List archived incidents"""
    model = IncidentArchive
    template_name = 'archives/incident_list.html'
    context_object_name = 'incidents'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = IncidentArchive.objects.all()
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(incident_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(incident_date__lte=end_date)
        
        # Filter by incident type
        incident_type = self.request.GET.get('incident_type')
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(incident_number__icontains=search) |
                Q(address__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-incident_date', '-incident_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incident_types'] = IncidentArchive.INCIDENT_TYPES
        return context


class IncidentArchiveDetail(LoginRequiredMixin, DetailView):
    """Detail view of archived incident"""
    model = IncidentArchive
    template_name = 'archives/incident_detail.html'
    context_object_name = 'incident'


class IncidentStatistics(LoginRequiredMixin, ListView):
    """Generate incident statistics"""
    template_name = 'archives/incident_stats.html'
    context_object_name = 'incidents'
    
    def get_queryset(self):
        return IncidentArchive.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get year filter
        year = self.request.GET.get('year', timezone.now().year)
        
        incidents = IncidentArchive.objects.filter(incident_date__year=year)
        
        # Statistics by type
        by_type = incidents.values('incident_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Statistics by month
        by_month = incidents.extra(
            select={'month': "EXTRACT(month FROM incident_date)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Average response times
        avg_times = incidents.aggregate(
            avg_response=Avg('response_time_minutes'),
            avg_turnout=Avg('turnout_time_minutes')
        )
        
        # Total calls
        total_calls = incidents.count()
        
        # Breakdown by type
        fire_calls = incidents.filter(incident_type='FIRE').count()
        ems_calls = incidents.filter(incident_type='EMS').count()
        mva_calls = incidents.filter(incident_type='MVA').count()
        
        context.update({
            'year': year,
            'total_calls': total_calls,
            'fire_calls': fire_calls,
            'ems_calls': ems_calls,
            'mva_calls': mva_calls,
            'by_type': by_type,
            'by_month': by_month,
            'avg_response_time': avg_times['avg_response'],
            'avg_turnout_time': avg_times['avg_turnout'],
            'available_years': IncidentArchive.objects.dates('incident_date', 'year', order='DESC'),
        })
        
        return context


class AnnualReportList(LoginRequiredMixin, ListView):
    """List annual reports"""
    model = AnnualReport
    template_name = 'archives/annual_reports.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        return AnnualReport.objects.all().order_by('-year')


class AnnualReportDetail(LoginRequiredMixin, DetailView):
    """View annual report"""
    model = AnnualReport
    template_name = 'archives/annual_report_detail.html'
    context_object_name = 'report'
    
    def get_object(self):
        return get_object_or_404(AnnualReport, year=self.kwargs['year'])


class EquipmentHistoryList(LoginRequiredMixin, ListView):
    """List equipment history"""
    model = EquipmentHistory
    template_name = 'archives/equipment_list.html'
    context_object_name = 'equipment'
    
    def get_queryset(self):
        queryset = EquipmentHistory.objects.all()
        
        # Filter by type
        eq_type = self.request.GET.get('type')
        if eq_type:
            queryset = queryset.filter(equipment_type=eq_type)
        
        # Filter by disposition
        disposition = self.request.GET.get('disposition')
        if disposition:
            queryset = queryset.filter(disposition=disposition)
        
        return queryset.order_by('-acquisition_date')


class EquipmentHistoryDetail(LoginRequiredMixin, DetailView):
    """Detail view of equipment history"""
    model = EquipmentHistory
    template_name = 'archives/equipment_detail.html'
    context_object_name = 'equipment'


class TimelineReport(LoginRequiredMixin, ListView):
    """Generate visual timeline of department history"""
    template_name = 'archives/timeline.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        # Get all events in chronological order
        events = []
        
        # Major incidents
        incidents = IncidentArchive.objects.filter(
            Q(fatalities__gt=0) | Q(property_damage__gte=100000)
        ).order_by('-incident_date')[:50]
        
        for incident in incidents:
            events.append({
                'date': incident.incident_date,
                'type': 'incident',
                'title': f"Major Incident: {incident.incident_number}",
                'description': incident.description[:200],
                'object': incident
            })
        
        # Equipment acquisitions/retirements
        equipment = EquipmentHistory.objects.all().order_by('-acquisition_date')[:50]
        
        for eq in equipment:
            events.append({
                'date': eq.acquisition_date,
                'type': 'equipment',
                'title': f"Acquired: {eq.equipment_name}",
                'description': f"{eq.equipment_type} - {eq.manufacturer}",
                'object': eq
            })
        
        # Legacy member separations (retirements, etc.)
        separations = LegacyMemberData.objects.filter(
            separation_type__in=['RETIRED', 'DECEASED']
        ).order_by('-separation_date')[:50]
        
        for member in separations:
            events.append({
                'date': member.separation_date,
                'type': 'member',
                'title': f"{member.get_separation_type_display()}: {member.first_name} {member.last_name}",
                'description': f"{member.years_of_service} years of service - {member.highest_rank}",
                'object': member
            })
        
        # Sort all events by date
        events.sort(key=lambda x: x['date'], reverse=True)
        
        return events


# Archivist/Admin Views

class AddHistoricalShift(IsArchivistMixin, CreateView):
    """Add historical shift record"""
    model = HistoricalShiftRecord
    form_class = HistoricalShiftRecordForm
    template_name = 'archives/add_shift.html'
    success_url = reverse_lazy('archives:shift_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f'Historical shift record added for {form.instance.shift_date}'
        )
        
        return response


class EditHistoricalShift(IsArchivistMixin, UpdateView):
    """Edit historical shift record"""
    model = HistoricalShiftRecord
    form_class = HistoricalShiftRecordForm
    template_name = 'archives/edit_shift.html'
    success_url = reverse_lazy('archives:shift_list')


class AddLegacyMember(IsArchivistMixin, CreateView):
    """Add legacy member record"""
    model = LegacyMemberData
    form_class = LegacyMemberDataForm
    template_name = 'archives/add_legacy_member.html'
    success_url = reverse_lazy('archives:legacy_members')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f'Legacy member record added for {form.instance.first_name} {form.instance.last_name}'
        )
        
        return response


class EditLegacyMember(IsArchivistMixin, UpdateView):
    """Edit legacy member record"""
    model = LegacyMemberData
    form_class = LegacyMemberDataForm
    template_name = 'archives/edit_legacy_member.html'
    success_url = reverse_lazy('archives:legacy_members')


class AddIncidentArchive(IsArchivistMixin, CreateView):
    """Add incident archive"""
    model = IncidentArchive
    form_class = IncidentArchiveForm
    template_name = 'archives/add_incident.html'
    success_url = reverse_lazy('archives:incident_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f'Incident {form.instance.incident_number} archived'
        )
        
        return response


class EditIncidentArchive(IsArchivistMixin, UpdateView):
    """Edit incident archive"""
    model = IncidentArchive
    form_class = IncidentArchiveForm
    template_name = 'archives/edit_incident.html'
    success_url = reverse_lazy('archives:incident_list')


class CreateAnnualReport(IsArchivistMixin, CreateView):
    """Create annual report"""
    model = AnnualReport
    form_class = AnnualReportForm
    template_name = 'archives/create_annual_report.html'
    
    def get_success_url(self):
        return reverse_lazy('archives:annual_report_detail', kwargs={'year': self.object.year})
    
    def get_initial(self):
        initial = super().get_initial()
        year = self.request.GET.get('year', timezone.now().year - 1)
        
        # Pre-populate statistics from incidents
        incidents = IncidentArchive.objects.filter(incident_date__year=year)
        
        initial.update({
            'year': year,
            'total_calls': incidents.count(),
            'fire_calls': incidents.filter(incident_type='FIRE').count(),
            'ems_calls': incidents.filter(incident_type='EMS').count(),
            'mva_calls': incidents.filter(incident_type='MVA').count(),
            'service_calls': incidents.filter(incident_type='SERVICE').count(),
            'false_alarms': incidents.filter(incident_type='FALSE_ALARM').count(),
        })
        
        # Calculate average times
        avg_times = incidents.aggregate(
            avg_response=Avg('response_time_minutes'),
            avg_turnout=Avg('turnout_time_minutes')
        )
        
        if avg_times['avg_response']:
            initial['avg_response_time'] = round(avg_times['avg_response'], 1)
        if avg_times['avg_turnout']:
            initial['avg_turnout_time'] = round(avg_times['avg_turnout'], 1)
        
        return initial
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f'Annual report created for {form.instance.year}'
        )
        
        return response


class EditAnnualReport(IsArchivistMixin, UpdateView):
    """Edit annual report"""
    model = AnnualReport
    form_class = AnnualReportForm
    template_name = 'archives/edit_annual_report.html'
    
    def get_object(self):
        return get_object_or_404(AnnualReport, year=self.kwargs['year'])
    
    def get_success_url(self):
        return reverse_lazy('archives:annual_report_detail', kwargs={'year': self.object.year})


class FinalizeAnnualReport(IsArchivistMixin, UpdateView):
    """Finalize annual report (lock it)"""
    model = AnnualReport
    fields = []
    template_name = 'archives/finalize_report.html'
    
    def get_object(self):
        return get_object_or_404(AnnualReport, year=self.kwargs['year'])
    
    def form_valid(self, form):
        report = form.save(commit=False)
        report.finalized = True
        report.save()
        
        messages.success(
            self.request,
            f'Annual report for {report.year} has been finalized and locked.'
        )
        
        return redirect('archives:annual_report_detail', year=report.year)


class AddEquipmentHistory(IsArchivistMixin, CreateView):
    """Add equipment history"""
    model = EquipmentHistory
    form_class = EquipmentHistoryForm
    template_name = 'archives/add_equipment.html'
    success_url = reverse_lazy('archives:equipment_list')


class EditEquipmentHistory(IsArchivistMixin, UpdateView):
    """Edit equipment history"""
    model = EquipmentHistory
    form_class = EquipmentHistoryForm
    template_name = 'archives/edit_equipment.html'
    success_url = reverse_lazy('archives:equipment_list')


# Search and Reports

class ArchiveSearch(LoginRequiredMixin, ListView):
    """Universal archive search"""
    template_name = 'archives/search_results.html'
    context_object_name = 'results'
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        
        if not query:
            return []
        
        results = []
        
        # Search incidents
        incidents = IncidentArchive.objects.filter(
            Q(incident_number__icontains=query) |
            Q(address__icontains=query) |
            Q(description__icontains=query)
        )[:20]
        
        for incident in incidents:
            results.append({
                'type': 'Incident',
                'title': incident.incident_number,
                'description': incident.description[:200],
                'date': incident.incident_date,
                'url': incident.get_absolute_url() if hasattr(incident, 'get_absolute_url') else None
            })
        
        # Search legacy members
        members = LegacyMemberData.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(badge_number__icontains=query)
        )[:20]
        
        for member in members:
            results.append({
                'type': 'Legacy Member',
                'title': f"{member.first_name} {member.last_name}",
                'description': f"Badge {member.badge_number} - {member.highest_rank}",
                'date': member.separation_date,
                'url': member.get_absolute_url() if hasattr(member, 'get_absolute_url') else None
            })
        
        # Search equipment
        equipment = EquipmentHistory.objects.filter(
            Q(equipment_name__icontains=query) |
            Q(unit_number__icontains=query)
        )[:20]
        
        for eq in equipment:
            results.append({
                'type': 'Equipment',
                'title': eq.equipment_name,
                'description': f"{eq.equipment_type} - {eq.manufacturer}",
                'date': eq.acquisition_date,
                'url': eq.get_absolute_url() if hasattr(eq, 'get_absolute_url') else None
            })
        
        return results
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
