"""
Custom middleware for security enforcement
"""
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from core.geo_security import GeoSecurityService
import logging

logger = logging.getLogger(__name__)


class GeographicSecurityMiddleware:
    """
    Middleware to enforce geographic IP restrictions
    Blocks all non-US IP addresses unless user has approved exception
    
    SECURITY FEATURES:
    - Automatic blocking of non-US IPs
    - Per-user temporary exceptions
    - Alert system for repeated attempts
    - Audit logging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs that should bypass geographic checking
        # (e.g., login page, static files, health checks)
        self.exempt_urls = [
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
        ]
    
    def __call__(self, request):
        # Skip if DEBUG mode (for development)
        if settings.DEBUG:
            return self.get_response(request)
        
        # Skip for exempt URLs
        if any(request.path.startswith(url) for url in self.exempt_urls):
            return self.get_response(request)
        
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            # For login page, we check AFTER authentication in the login view
            return self.get_response(request)
        
        # Get client IP
        ip_address = self._get_client_ip(request)
        
        # Check geographic access
        is_allowed, reason, geo = GeoSecurityService.check_ip_access(
            ip_address, 
            request.user, 
            request
        )
        
        if not is_allowed:
            # Access denied - show blocked page
            logger.warning(
                f"Geographic access blocked: {request.user.username} from "
                f"{ip_address} ({geo.country_name if geo else 'Unknown'})"
            )
            
            # Return blocked page
            return render(request, 'security/geographic_blocked.html', {
                'reason': reason,
                'ip_address': ip_address,
                'country': geo.country_name if geo else 'Unknown',
                'city': geo.city if geo else '',
            }, status=403)
        
        # Access allowed - continue
        response = self.get_response(request)
        return response
    
    def _get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net code.jquery.com; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' cdn.jsdelivr.net; "
                "frame-ancestors 'none';"
            )
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
