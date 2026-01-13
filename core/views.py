"""
Core application views including setup wizard
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from django.utils import timezone  # <-- ADDED MISSING IMPORT
from core.system_config import SystemConfiguration
from django.db import transaction


class SystemConfigurationForm(forms.ModelForm):
    """
    Form for initial system configuration
    """
    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Please explain why you are changing the country configuration (required for country changes)"
    )
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'department_name',
            'department_abbreviation',
            'timezone',
            'primary_country',
            'secondary_country',
            'geo_security_enabled',
            'admin_email',
            'it_email',
            'security_email',
        ]
        widgets = {
            'department_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Volunteer Fire Department'
            }),
            'department_abbreviation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., VFD'
            }),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
            'primary_country': forms.Select(attrs={'class': 'form-control'}),
            'secondary_country': forms.Select(attrs={'class': 'form-control'}),
            'admin_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'admin@yourfiredept.org'
            }),
            'it_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'it@yourfiredept.org'
            }),
            'security_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'security@yourfiredept.org'
            }),
        }
        help_texts = {
            'primary_country': '🟢 Users from this country can access automatically',
            'secondary_country': '🔵 Optional: For departments on country borders (e.g., US-Canada)',
            'geo_security_enabled': 'When enabled, only users from allowed countries can access',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add timezone choices
        import pytz
        timezone_choices = [(tz, tz) for tz in pytz.common_timezones]
        self.fields['timezone'].widget = forms.Select(
            choices=timezone_choices,
            attrs={'class': 'form-control'}
        )
        
        # Make secondary country optional
        self.fields['secondary_country'].required = False
        
        # Add Bootstrap styling
        for field_name, field in self.fields.items():
            if field_name != 'geo_security_enabled':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'
    
    def clean(self):
        cleaned_data = super().clean()
        primary = cleaned_data.get('primary_country')
        secondary = cleaned_data.get('secondary_country')
        
        # Validate that primary and secondary are different
        if primary and secondary and primary == secondary:
            raise forms.ValidationError(
                "Primary and secondary countries must be different."
            )
        
        return cleaned_data


class SetupWizardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Initial setup wizard for system configuration
    Only accessible to superusers or during first-time setup
    """
    template_name = 'setup_wizard.html'
    
    def test_func(self):
        """Only allow superusers"""
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        config = SystemConfiguration.get_config()
        
        if self.request.method == 'POST':
            form = SystemConfigurationForm(self.request.POST, instance=config)
        else:
            form = SystemConfigurationForm(instance=config)
        
        context['form'] = form
        context['config'] = config
        context['is_initial_setup'] = not config.setup_completed
        
        return context
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        config = SystemConfiguration.get_config()
        form = SystemConfigurationForm(request.POST, instance=config)
        
        if form.is_valid():
            # Save configuration
            config = form.save(commit=False)
            
            # Mark setup as completed if this is first time
            if not config.setup_completed:
                config.setup_completed = True
                config.setup_completed_at = timezone.now()
                config.setup_completed_by = request.user
            
            # Set changed_by for country changes
            if 'primary_country' in form.changed_data:
                config.primary_country_changed_by = request.user
            if 'secondary_country' in form.changed_data:
                config.secondary_country_changed_by = request.user
            
            config.save()
            
            messages.success(
                request,
                '✅ System configuration saved successfully! '
                'Leadership team has been notified of any security changes.'
            )
            
            return redirect('home')
        
        # Form invalid - show errors
        return render(request, self.template_name, self.get_context_data(form=form))


class SystemStatusView(LoginRequiredMixin, TemplateView):
    """
    Display current system configuration and status
    """
    template_name = 'system_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        config = SystemConfiguration.get_config()
        
        context['config'] = config
        context['allowed_countries'] = config.get_allowed_country_names()
        
        # Get recent country changes
        from core.system_config import CountryChangeLog
        context['recent_changes'] = CountryChangeLog.objects.all()[:10]
        
        # Get geo security statistics
        from core.geo_security import IPGeolocation, SuspiciousAccessAttempt
        from datetime import timedelta
        
        last_30_days = timezone.now() - timedelta(days=30)
        
        context['stats'] = {
            'total_ips': IPGeolocation.objects.count(),
            'unique_countries': IPGeolocation.objects.values('country_code').distinct().count(),
            'blocked_attempts': SuspiciousAccessAttempt.objects.filter(
                timestamp__gte=last_30_days,
                was_blocked=True
            ).count(),
        }
        
        return context


@login_required
@user_passes_test(lambda u: u.is_superuser)
def test_geolocation(request):
    """
    Test geolocation service (superuser only)
    """
    from core.geo_security import GeoSecurityService
    
    test_ips = {
        'Google DNS (US)': '8.8.8.8',
        'Cloudflare (US)': '1.1.1.1',
        'Sample IP': request.GET.get('ip', '8.8.4.4')
    }
    
    results = {}
    for name, ip in test_ips.items():
        geo = GeoSecurityService.get_ip_geolocation(ip)
        if geo:
            results[name] = {
                'ip': ip,
                'country': geo.country_name,
                'city': geo.city,
                'allowed': SystemConfiguration.get_config().is_country_allowed(geo.country_code)
            }
    
    return render(request, 'test_geolocation.html', {'results': results})
