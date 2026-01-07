"""
Django admin configuration for core security models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from core.geo_security import (
    IPGeolocation, 
    InternationalAccessException, 
    SuspiciousAccessAttempt
)
from core.system_config import SystemConfiguration, CountryChangeLog
from core.audit import AuditLog, LoginAttempt
from core.notifications import NotificationManager, NotificationType, NotificationPriority


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for system configuration
    CRITICAL: Changes here affect security for entire system
    """
    list_display = [
        'department_name', 
        'primary_country_display', 
        'secondary_country_display',
        'geo_security_status',
        'modified_at'
    ]
    
    fieldsets = (
        ('Department Information', {
            'fields': ('department_name', 'department_abbreviation', 'timezone')
        }),
        ('Geographic Security Settings', {
            'fields': (
                'geo_security_enabled',
                'primary_country',
                'secondary_country',
            ),
            'description': (
                '<div style="background: #fff3cd; padding: 15px; border: 2px solid #ffc107; border-radius: 5px;">'
                '<strong>⚠️ CRITICAL SECURITY SETTINGS</strong><br>'
                'Changes to these settings affect ALL users immediately.<br>'
                'Leadership team will be notified of any changes.<br><br>'
                '<strong>Primary Country:</strong> Users from this country can access automatically.<br>'
                '<strong>Secondary Country:</strong> Optional. Useful for border departments.<br>'
                '<strong>Example:</strong> Department on US-Canada border sets Primary=US, Secondary=CA'
                '</div>'
            )
        }),
        ('Change History - Primary Country', {
            'fields': (
                'previous_primary_country',
                'primary_country_changed_at',
                'primary_country_changed_by'
            ),
            'classes': ('collapse',),
            'description': 'Read-only tracking of primary country changes'
        }),
        ('Change History - Secondary Country', {
            'fields': (
                'previous_secondary_country',
                'secondary_country_changed_at',
                'secondary_country_changed_by'
            ),
            'classes': ('collapse',),
            'description': 'Read-only tracking of secondary country changes'
        }),
        ('Contact Information', {
            'fields': ('admin_email', 'it_email', 'security_email'),
            'classes': ('collapse',)
        }),
        ('Setup Information', {
            'fields': ('setup_completed', 'setup_completed_at', 'setup_completed_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'previous_primary_country', 'primary_country_changed_at', 'primary_country_changed_by',
        'previous_secondary_country', 'secondary_country_changed_at', 'secondary_country_changed_by',
        'setup_completed_at', 'setup_completed_by'
    ]
    
    def has_add_permission(self, request):
        # Only one configuration record allowed
        return not SystemConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Cannot delete system configuration
        return False
    
    def primary_country_display(self, obj):
        """Display primary country with flag"""
        country_name = dict(obj.COUNTRY_CHOICES).get(obj.primary_country, obj.primary_country)
        return format_html(
            '<strong style="color: green;">🟢 {}</strong>',
            country_name
        )
    primary_country_display.short_description = 'Primary Country'
    
    def secondary_country_display(self, obj):
        """Display secondary country with flag"""
        if obj.secondary_country:
            country_name = dict(obj.COUNTRY_CHOICES).get(obj.secondary_country, obj.secondary_country)
            return format_html(
                '<span style="color: blue;">🔵 {}</span>',
                country_name
            )
        return format_html('<span style="color: gray;">Not configured</span>')
    secondary_country_display.short_description = 'Secondary Country'
    
    def geo_security_status(self, obj):
        """Display geo security status"""
        if obj.geo_security_enabled:
            return format_html('<span style="color: green; font-weight: bold;">✅ ENABLED</span>')
        return format_html('<span style="color: red; font-weight: bold;">❌ DISABLED</span>')
    geo_security_status.short_description = 'Geo Security'
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """Track country changes and set changed_by user"""
        if change:
            old_obj = SystemConfiguration.objects.get(pk=obj.pk)
            
            # Track primary country change
            if old_obj.primary_country != obj.primary_country:
                obj.primary_country_changed_by = request.user
                
                # Log to CountryChangeLog
                CountryChangeLog.log_change(
                    'PRIMARY',
                    old_obj.primary_country,
                    obj.primary_country,
                    request.user,
                    request,
                    reason=request.POST.get('change_reason', 'Changed via admin panel')
                )
            
            # Track secondary country change
            if old_obj.secondary_country != obj.secondary_country:
                obj.secondary_country_changed_by = request.user
                
                # Log to CountryChangeLog
                CountryChangeLog.log_change(
                    'SECONDARY',
                    old_obj.secondary_country or '',
                    obj.secondary_country or '',
                    request.user,
                    request,
                    reason=request.POST.get('change_reason', 'Changed via admin panel')
                )
        
        super().save_model(request, obj, form, change)
        
        # Show success message with security warning
        if change:
            messages.warning(
                request,
                format_html(
                    '<strong>⚠️ SECURITY CONFIGURATION UPDATED</strong><br>'
                    'Leadership team has been notified via email.<br>'
                    'Changes are effective immediately for all users.'
                )
            )


@admin.register(CountryChangeLog)
class CountryChangeLogAdmin(admin.ModelAdmin):
    """
    Immutable audit log of country configuration changes
    
    SECURITY FEATURES:
    - Read-only (no edits allowed)
    - No deletions allowed
    - Tamper attempts logged and alerted
    - Checksum verification
    """
    list_display = [
        'timestamp', 
        'change_type', 
        'old_value_display',
        'new_value_display',
        'changed_by',
        'integrity_status',
        'leadership_notified'
    ]
    list_filter = ['change_type', 'leadership_notified', 'timestamp']
    search_fields = ['changed_by__username', 'change_reason', 'checksum']
    readonly_fields = [
        'timestamp', 'changed_by', 'change_type', 'old_value', 'new_value',
        'ip_address', 'user_agent', 'leadership_notified', 'leadership_notified_at',
        'notification_recipient_count', 'change_reason', 'is_locked', 'created_at',
        'checksum', 'integrity_verification'
    ]
    
    fieldsets = (
        ('⚠️ IMMUTABLE AUDIT RECORD', {
            'description': (
                '<div style="background: #dc3545; color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">'
                '<strong>CRITICAL SECURITY NOTICE</strong><br>'
                'This audit log record is IMMUTABLE and cannot be modified or deleted.<br>'
                'Any tampering attempts are logged and IT Director is immediately alerted.<br>'
                'This record is protected by cryptographic checksum verification.'
                '</div>'
            ),
            'fields': ('is_locked', 'checksum', 'integrity_verification')
        }),
        ('Change Details', {
            'fields': ('timestamp', 'changed_by', 'change_type', 'old_value', 'new_value')
        }),
        ('Justification', {
            'fields': ('change_reason',)
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Notification Status', {
            'fields': ('leadership_notified', 'leadership_notified_at', 'notification_recipient_count'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_integrity_action']
    
    def has_add_permission(self, request):
        # Logs are created automatically by system only
        return False
    
    def has_change_permission(self, request, obj=None):
        # No one can edit - not even superusers
        return False
    
    def has_delete_permission(self, request, obj=None):
        # NEVER allow deletion - not even superusers
        return False
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Override to show warning message on detail view"""
        extra_context = extra_context or {}
        extra_context['show_save'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        extra_context['show_delete'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def old_value_display(self, obj):
        """Display old value with country name"""
        if obj.change_type in ['PRIMARY', 'SECONDARY']:
            country_name = dict(SystemConfiguration.COUNTRY_CHOICES).get(obj.old_value, obj.old_value)
            return country_name if country_name else 'None'
        return obj.old_value
    old_value_display.short_description = 'Previous Value'
    
    def new_value_display(self, obj):
        """Display new value with country name"""
        if obj.change_type in ['PRIMARY', 'SECONDARY']:
            country_name = dict(SystemConfiguration.COUNTRY_CHOICES).get(obj.new_value, obj.new_value)
            return country_name if country_name else 'None'
        return obj.new_value
    new_value_display.short_description = 'New Value'
    
    def integrity_status(self, obj):
        """Display integrity verification status"""
        is_valid = obj.verify_integrity()
        if is_valid:
            return format_html('<span style="color: green; font-weight: bold;">✅ VALID</span>')
        return format_html('<span style="color: red; font-weight: bold;">❌ TAMPERED</span>')
    integrity_status.short_description = 'Integrity'
    
    def integrity_verification(self, obj):
        """Detailed integrity verification"""
        is_valid = obj.verify_integrity()
        if is_valid:
            return format_html(
                '<div style="background: #d4edda; padding: 10px; border-radius: 5px;">'
                '<strong style="color: green;">✅ INTEGRITY VERIFIED</strong><br>'
                'Checksum: <code>{}</code><br>'
                'This record has not been tampered with.'
                '</div>',
                obj.checksum
            )
        return format_html(
            '<div style="background: #f8d7da; padding: 10px; border-radius: 5px;">'
            '<strong style="color: red;">❌ INTEGRITY FAILURE</strong><br>'
            'Stored Checksum: <code>{}</code><br>'
            '⚠️ WARNING: This record may have been tampered with!<br>'
            'IT Director has been notified.'
            '</div>',
            obj.checksum
        )
    integrity_verification.short_description = 'Integrity Verification'
    
    def verify_integrity_action(self, request, queryset):
        """Bulk action to verify integrity of selected records"""
        results = {
            'total': 0,
            'valid': 0,
            'invalid': 0
        }
        
        for log in queryset:
            results['total'] += 1
            if log.verify_integrity():
                results['valid'] += 1
            else:
                results['invalid'] += 1
        
        if results['invalid'] > 0:
            self.message_user(
                request,
                format_html(
                    '<strong>⚠️ INTEGRITY CHECK FAILED</strong><br>'
                    'Valid: {} | Invalid: {} | Total: {}<br>'
                    'Invalid records may have been tampered with. IT Director has been notified.',
                    results['valid'], results['invalid'], results['total']
                ),
                level=messages.ERROR
            )
        else:
            self.message_user(
                request,
                f"✅ All {results['total']} records passed integrity verification.",
                level=messages.SUCCESS
            )
    verify_integrity_action.short_description = '🔍 Verify Integrity of Selected Records'


@admin.register(IPGeolocation)
class IPGeolocationAdmin(admin.ModelAdmin):
    list_display = [
        'ip_address', 'country_flag', 'country_name', 'city', 
        'access_count', 'last_seen', 'is_suspicious_display'
    ]
    list_filter = ['country_code', 'is_proxy', 'is_vpn', 'is_tor']
    search_fields = ['ip_address', 'country_name', 'city', 'isp']
    readonly_fields = [
        'ip_address', 'country_code', 'country_name', 'region', 'city',
        'isp', 'organization', 'latitude', 'longitude', 'lookup_date',
        'last_seen', 'access_count', 'is_proxy', 'is_vpn', 'is_tor', 'threat_level'
    ]
    
    def has_add_permission(self, request):
        # Geolocation records are created automatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion of old records
        return True
    
    def country_flag(self, obj):
        """Display country flag emoji"""
        flags = {
            'US': '🇺🇸', 'GB': '🇬🇧', 'CA': '🇨🇦', 'MX': '🇲🇽',
            'DE': '🇩🇪', 'FR': '🇫🇷', 'CN': '🇨🇳', 'RU': '🇷🇺',
        }
        flag = flags.get(obj.country_code, '🌍')
        return format_html('<span style="font-size: 1.5em;">{}</span>', flag)
    country_flag.short_description = 'Flag'
    
    def is_suspicious_display(self, obj):
        """Display suspicious indicator"""
        if obj.is_suspicious:
            return format_html('<span style="color: red;">⚠️ SUSPICIOUS</span>')
        return format_html('<span style="color: green;">✓ Clean</span>')
    is_suspicious_display.short_description = 'Status'


@admin.register(InternationalAccessException)
class InternationalAccessExceptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'destination_country', 'status_display', 
        'start_date', 'end_date', 'times_used', 'approved_by'
    ]
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'destination_country']
    readonly_fields = [
        'requested_by', 'requested_at', 'approved_by', 'approved_at',
        'times_used', 'last_used'
    ]
    
    fieldsets = (
        ('User & Destination', {
            'fields': ('user', 'destination_country', 'reason')
        }),
        ('Time Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Approval', {
            'fields': ('status', 'admin_notes', 'approved_by', 'approved_at')
        }),
        ('Usage Tracking', {
            'fields': ('times_used', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Request Info', {
            'fields': ('requested_by', 'requested_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_exceptions', 'deny_exceptions', 'revoke_exceptions']
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'PENDING': 'orange',
            'APPROVED': 'green',
            'DENIED': 'red',
            'EXPIRED': 'gray',
            'REVOKED': 'darkred',
        }
        color = colors.get(obj.status, 'black')
        
        # Check if should be expired
        obj.check_and_update_status()
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        """Handle approval workflow"""
        if change:
            # Check if status changed to APPROVED
            old_obj = InternationalAccessException.objects.get(pk=obj.pk)
            if old_obj.status != 'APPROVED' and obj.status == 'APPROVED':
                # Set approval info
                obj.approved_by = request.user
                obj.approved_at = timezone.now()
                
                # Notify user
                self._notify_user_approved(obj)
        
        super().save_model(request, obj, form, change)
    
    def approve_exceptions(self, request, queryset):
        """Bulk approve exceptions"""
        count = 0
        for exception in queryset.filter(status='PENDING'):
            exception.status = 'APPROVED'
            exception.approved_by = request.user
            exception.approved_at = timezone.now()
            exception.save()
            
            # Notify user
            self._notify_user_approved(exception)
            count += 1
        
        self.message_user(request, f'{count} exception(s) approved.', messages.SUCCESS)
    approve_exceptions.short_description = 'Approve selected exceptions'
    
    def deny_exceptions(self, request, queryset):
        """Bulk deny exceptions"""
        count = queryset.filter(status='PENDING').update(
            status='DENIED',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} exception(s) denied.', messages.WARNING)
    deny_exceptions.short_description = 'Deny selected exceptions'
    
    def revoke_exceptions(self, request, queryset):
        """Revoke active exceptions"""
        count = queryset.filter(status='APPROVED').update(status='REVOKED')
        self.message_user(request, f'{count} exception(s) revoked.', messages.ERROR)
    revoke_exceptions.short_description = 'Revoke selected exceptions'
    
    def _notify_user_approved(self, exception):
        """Send notification to user when exception is approved"""
        NotificationManager.send_notification(
            notification_type=NotificationType.APPROVAL_NEEDED,
            recipients=[exception.user],
            subject="International Access Approved",
            message=f"""
Your request for international access has been APPROVED.

Destination: {exception.destination_country}
Valid From: {exception.start_date.strftime('%Y-%m-%d %H:%M')}
Valid Until: {exception.end_date.strftime('%Y-%m-%d %H:%M')}

You can now access the system from {exception.destination_country} during this time period.

If you have any issues, please contact IT support.
            """.strip(),
            priority=NotificationPriority.HIGH
        )


@admin.register(SuspiciousAccessAttempt)
class SuspiciousAccessAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'ip_address', 'country_display',
        'attempt_type', 'was_blocked', 'it_notified', 'resolved'
    ]
    list_filter = [
        'attempt_type', 'was_blocked', 'it_notified', 'resolved', 'timestamp'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 
        'ip_address'
    ]
    readonly_fields = [
        'timestamp', 'user', 'ip_address', 'geolocation', 'attempt_type',
        'was_blocked', 'user_agent', 'details', 'it_notified', 'it_notified_at'
    ]
    
    fieldsets = (
        ('Attempt Details', {
            'fields': ('timestamp', 'user', 'ip_address', 'geolocation', 'attempt_type', 'was_blocked')
        }),
        ('Technical Details', {
            'fields': ('user_agent', 'details'),
            'classes': ('collapse',)
        }),
        ('Notification', {
            'fields': ('it_notified', 'it_notified_at')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
    )
    
    actions = ['mark_resolved', 'create_exception']
    
    def has_add_permission(self, request):
        # Suspicious attempts are logged automatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Keep for forensics
        return False
    
    def country_display(self, obj):
        """Display country with flag"""
        if obj.geolocation:
            return f"{obj.geolocation.country_name}"
        return "Unknown"
    country_display.short_description = 'Country'
    
    def mark_resolved(self, request, queryset):
        """Mark attempts as resolved"""
        count = queryset.update(
            resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{count} attempt(s) marked as resolved.', messages.SUCCESS)
    mark_resolved.short_description = 'Mark as resolved'
    
    def create_exception(self, request, queryset):
        """Create international access exception from attempt"""
        if queryset.count() != 1:
            self.message_user(
                request, 
                'Please select exactly one attempt to create an exception.', 
                messages.ERROR
            )
            return
        
        attempt = queryset.first()
        
        # Create exception (7 days by default)
        exception = InternationalAccessException.objects.create(
            user=attempt.user,
            destination_country=attempt.geolocation.country_name if attempt.geolocation else 'Unknown',
            reason='Created from suspicious access attempt',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=7),
            requested_by=request.user,
            status='PENDING'
        )
        
        # Redirect to edit the exception
        url = reverse('admin:core_internationalaccessexception_change', args=[exception.pk])
        self.message_user(
            request,
            format_html(
                'Exception created. <a href="{}">Click here to review and approve</a>.',
                url
            ),
            messages.SUCCESS
        )
    create_exception.short_description = 'Create access exception'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'action', 'ip_address', 
        'risk_level_display', 'success'
    ]
    list_filter = ['action', 'risk_level', 'success', 'timestamp']
    search_fields = ['user__username', 'ip_address', 'details']
    readonly_fields = [
        'timestamp', 'user', 'action', 'content_type', 'object_id',
        'ip_address', 'user_agent', 'details', 'success', 'risk_level'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Audit logs are created automatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # NEVER allow deletion of audit logs
        return False
    
    def risk_level_display(self, obj):
        """Display risk level with color"""
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred',
        }
        color = colors.get(obj.risk_level, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_risk_level_display()
        )
    risk_level_display.short_description = 'Risk Level'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'ip_address', 'success', 'failure_reason']
    list_filter = ['success', 'timestamp']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['timestamp', 'username', 'ip_address', 'user_agent', 'success', 'failure_reason']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Can delete old login attempts (keep for 90 days)
        return True
