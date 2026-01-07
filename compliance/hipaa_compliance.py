"""
HIPAA Compliance Checking and Reporting
Automated compliance monitoring and alerting
"""
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .hipaa_models import HIPAATraining, BusinessAssociate, SecurityBreach, EmergencyAccess
import logging

logger = logging.getLogger(__name__)


class HIPAAComplianceChecker:
    """
    Check and report on HIPAA compliance status
    """
    
    @classmethod
    def run_daily_checks(cls):
        """
        Run daily compliance checks
        Should be scheduled as daily task
        
        Returns:
            dict: Results of compliance checks
        """
        results = {
            'training_compliance': cls.check_training_compliance(),
            'baa_compliance': cls.check_baa_compliance(),
            'breach_notifications': cls.check_breach_notifications(),
            'emergency_access': cls.check_emergency_access_review(),
        }
        
        # Send alerts if needed
        cls._send_compliance_alerts(results)
        
        return results
    
    @classmethod
    def check_training_compliance(cls):
        """
        Check if all workforce members have current HIPAA training
        
        Returns:
            dict: Training compliance status
        """
        total_staff = User.objects.filter(is_active=True).count()
        
        # Find staff with current training
        current_training = HIPAATraining.objects.filter(
            completed=True,
            expiration_date__gte=timezone.now().date()
        ).values_list('user_id', flat=True).distinct()
        
        trained_staff = len(set(current_training))
        
        # Find staff with expired or no training
        untrained_staff = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=current_training
        )
        
        # Find training expiring soon (30 days)
        expiring_soon = HIPAATraining.objects.filter(
            completed=True,
            expiration_date__gte=timezone.now().date(),
            expiration_date__lte=timezone.now().date() + timedelta(days=30)
        )
        
        compliance_rate = (trained_staff / total_staff * 100) if total_staff > 0 else 0
        
        return {
            'total_staff': total_staff,
            'trained_staff': trained_staff,
            'untrained_staff': list(untrained_staff),
            'expiring_soon': list(expiring_soon),
            'compliance_rate': compliance_rate,
            'is_compliant': compliance_rate == 100
        }
    
    @classmethod
    def check_baa_compliance(cls):
        """
        Check Business Associate Agreement compliance
        
        Returns:
            dict: BAA compliance status
        """
        total_bas = BusinessAssociate.objects.filter(is_active=True).count()
        
        # BAAs expiring soon (30 days)
        expiring_soon = BusinessAssociate.objects.filter(
            is_active=True,
            agreement_expires__gte=timezone.now().date(),
            agreement_expires__lte=timezone.now().date() + timedelta(days=30)
        )
        
        # Expired BAAs
        expired = BusinessAssociate.objects.filter(
            is_active=True,
            agreement_expires__lt=timezone.now().date()
        )
        
        # Missing BAA documents
        missing_documents = BusinessAssociate.objects.filter(
            is_active=True,
            baa_signed=False
        )
        
        return {
            'total_bas': total_bas,
            'expiring_soon': list(expiring_soon),
            'expired': list(expired),
            'missing_documents': list(missing_documents),
            'is_compliant': expired.count() == 0 and missing_documents.count() == 0
        }
    
    @classmethod
    def check_breach_notifications(cls):
        """
        Check if breach notifications are overdue
        
        Returns:
            dict: Breach notification status
        """
        # Active breaches (not fully resolved)
        active_breaches = SecurityBreach.objects.filter(
            investigation_complete=False
        )
        
        # Overdue notifications (60-day deadline)
        overdue_notifications = []
        for breach in active_breaches:
            if breach.is_notification_overdue:
                overdue_notifications.append(breach)
        
        # Breaches needing review
        needs_review = SecurityBreach.objects.filter(
            investigation_complete=False,
            investigation_started__isnull=True
        )
        
        return {
            'active_breaches': active_breaches.count(),
            'overdue_notifications': overdue_notifications,
            'needs_review': list(needs_review),
            'is_compliant': len(overdue_notifications) == 0
        }
    
    @classmethod
    def check_emergency_access_review(cls):
        """
        Check if emergency accesses need supervisory review
        
        Returns:
            dict: Emergency access review status
        """
        # Emergency accesses in last 7 days
        recent_accesses = EmergencyAccess.objects.filter(
            accessed_at__gte=timezone.now() - timedelta(days=7)
        )
        
        # Accesses needing review
        needs_review = recent_accesses.filter(
            reviewed_by__isnull=True
        )
        
        # Accesses > 24 hours old without review
        overdue_review = needs_review.filter(
            accessed_at__lt=timezone.now() - timedelta(days=1)
        )
        
        return {
            'recent_accesses': recent_accesses.count(),
            'needs_review': needs_review.count(),
            'overdue_review': list(overdue_review),
            'is_compliant': overdue_review.count() == 0
        }
    
    @classmethod
    def _send_compliance_alerts(cls, results):
        """
        Send alerts for compliance issues
        
        Args:
            results: Results from compliance checks
        """
        alerts = []
        
        # Training compliance alerts
        training = results['training_compliance']
        if not training['is_compliant']:
            alerts.append({
                'priority': 'HIGH',
                'subject': f"HIPAA Training Compliance Alert - {training['compliance_rate']:.1f}%",
                'message': f"{len(training['untrained_staff'])} staff members need HIPAA training."
            })
        
        if training['expiring_soon']:
            alerts.append({
                'priority': 'MEDIUM',
                'subject': f"HIPAA Training Expiring Soon - {len(training['expiring_soon'])} staff",
                'message': f"{len(training['expiring_soon'])} staff members have training expiring within 30 days."
            })
        
        # BAA compliance alerts
        baa = results['baa_compliance']
        if baa['expired']:
            alerts.append({
                'priority': 'CRITICAL',
                'subject': f"Expired Business Associate Agreements - {len(baa['expired'])}",
                'message': f"{len(baa['expired'])} Business Associate Agreements have expired!"
            })
        
        if baa['expiring_soon']:
            alerts.append({
                'priority': 'HIGH',
                'subject': f"BAAs Expiring Soon - {len(baa['expiring_soon'])}",
                'message': f"{len(baa['expiring_soon'])} Business Associate Agreements expire within 30 days."
            })
        
        # Breach notification alerts
        breach = results['breach_notifications']
        if breach['overdue_notifications']:
            alerts.append({
                'priority': 'CRITICAL',
                'subject': f"OVERDUE Breach Notifications - {len(breach['overdue_notifications'])}",
                'message': f"{len(breach['overdue_notifications'])} breach notifications are past the 60-day deadline!"
            })
        
        # Emergency access alerts
        emergency = results['emergency_access']
        if emergency['overdue_review']:
            alerts.append({
                'priority': 'HIGH',
                'subject': f"Emergency Access Needs Review - {len(emergency['overdue_review'])}",
                'message': f"{len(emergency['overdue_review'])} emergency accesses need supervisory review."
            })
        
        # Send alerts
        if alerts:
            cls._send_alert_email(alerts)
    
    @classmethod
    def _send_alert_email(cls, alerts):
        """Send compliance alert email"""
        from core.notifications import NotificationManager, NotificationType, NotificationPriority
        
        # Get compliance officers
        compliance_officers = User.objects.filter(
            groups__name__in=['Compliance Officers', 'Chief Officers'],
            is_active=True
        ).distinct()
        
        if not compliance_officers:
            logger.error("No compliance officers found to send HIPAA alerts")
            return
        
        # Build message
        subject = "🏥 HIPAA Compliance Alert"
        
        message = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HIPAA COMPLIANCE ALERTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The following HIPAA compliance issues require attention:

"""
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        alerts.sorted(key=lambda x: priority_order.get(x['priority'], 4))
        
        for alert in alerts:
            icon = '🚨' if alert['priority'] == 'CRITICAL' else '⚠️' if alert['priority'] == 'HIGH' else 'ℹ️'
            message += f"""
{icon} {alert['priority']}: {alert['subject']}
{alert['message']}
{'─' * 60}
"""
        
        message += """
ACTION REQUIRED:
1. Review each alert
2. Take corrective action
3. Document resolution
4. Update compliance records

Access compliance dashboard:
Admin Panel → Compliance → HIPAA Compliance Dashboard

Contact:
  Compliance Officer: compliance@yourfiredept.org
  IT Director: it@yourfiredept.org

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated HIPAA compliance alert.
        """.strip()
        
        # Determine priority
        has_critical = any(a['priority'] == 'CRITICAL' for a in alerts)
        priority = NotificationPriority.URGENT if has_critical else NotificationPriority.HIGH
        
        NotificationManager.send_notification(
            notification_type=NotificationType.GENERAL_ANNOUNCEMENT,
            recipients=list(compliance_officers),
            subject=subject,
            message=message,
            priority=priority
        )
    
    @classmethod
    def generate_compliance_report(cls):
        """
        Generate comprehensive HIPAA compliance report
        
        Returns:
            dict: Complete compliance report
        """
        report = {
            'generated_at': timezone.now(),
            'training': cls.check_training_compliance(),
            'baa': cls.check_baa_compliance(),
            'breaches': cls.check_breach_notifications(),
            'emergency_access': cls.check_emergency_access_review(),
        }
        
        # Calculate overall compliance score
        checks = [
            report['training']['is_compliant'],
            report['baa']['is_compliant'],
            report['breaches']['is_compliant'],
            report['emergency_access']['is_compliant'],
        ]
        
        report['overall_compliance_rate'] = (sum(checks) / len(checks) * 100)
        report['is_compliant'] = all(checks)
        
        return report


# Scheduled task function
def run_hipaa_compliance_checks():
    """
    Scheduled task to run HIPAA compliance checks
    Should run daily at 7:00 AM
    """
    logger.info("Running HIPAA compliance checks...")
    
    try:
        results = HIPAAComplianceChecker.run_daily_checks()
        
        logger.info(
            f"HIPAA compliance check complete. "
            f"Training: {results['training_compliance']['compliance_rate']:.1f}%, "
            f"BAA: {'✓' if results['baa_compliance']['is_compliant'] else '✗'}, "
            f"Breaches: {results['breach_notifications']['active_breaches']}, "
            f"Emergency Access: {results['emergency_access']['needs_review']}"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"HIPAA compliance check failed: {e}")
        raise
