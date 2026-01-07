"""
Django admin configuration for core security models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from core.geo_security import (
    IPGeolocation, 
    InternationalAccessException, 
    SuspiciousAccessAttempt
)
from core.audit import AuditLog, LoginAttempt
from core.notifications import NotificationManager, NotificationType, NotificationPriority


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
