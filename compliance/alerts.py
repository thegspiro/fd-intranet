"""
Compliance Alert Service
Monitors compliance items and sends alerts for expiring/overdue items
"""
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import MedicalPhysical, FitTest, Immunization, ComplianceAlert
from core.notifications import NotificationManager, NotificationType, NotificationPriority
import logging

logger = logging.getLogger(__name__)


class ComplianceAlertService:
    """
    Service for monitoring compliance and sending alerts
    """
    
    # Alert thresholds (days before expiration)
    WARNING_DAYS = 30
    URGENT_DAYS = 7
    
    @classmethod
    def check_all_compliance(cls):
        """
        Main method to check all compliance items for all active members
        Run this as a scheduled task (daily)
        """
        active_members = User.objects.filter(is_active=True)
        alerts_sent = 0
        
        for member in active_members:
            alerts_sent += cls.check_member_physicals(member)
            alerts_sent += cls.check_member_fit_tests(member)
            alerts_sent += cls.check_member_immunizations(member)
        
        logger.info(f"Compliance check complete. Sent {alerts_sent} alerts.")
        return alerts_sent
    
    @classmethod
    def check_member_physicals(cls, member):
        """Check if member's physical is expiring or overdue"""
        alerts_sent = 0
        today = timezone.now().date()
        
        # Get most recent physical
        latest_physical = MedicalPhysical.objects.filter(
            user=member,
            result__in=['CLEARED', 'CLEARED_WITH_RESTRICTIONS']
        ).order_by('-exam_date').first()
        
        if not latest_physical:
            # No physical on file - send alert
            alerts_sent += cls._send_alert(
                member,
                'PHYSICAL',
                'Medical Physical Required',
                'You do not have a current medical physical on file. Please schedule your physical examination.',
                priority=NotificationPriority.HIGH
            )
            return alerts_sent
        
        # Check if overdue
        if latest_physical.next_exam_due < today:
            days_overdue = (today - latest_physical.next_exam_due).days
            alerts_sent += cls._send_alert(
                member,
                'PHYSICAL',
                'Medical Physical OVERDUE',
                f'Your medical physical is {days_overdue} days overdue. Please schedule immediately.',
                priority=NotificationPriority.URGENT,
                related_id=latest_physical.pk
            )
        
        # Check if expiring soon
        elif latest_physical.next_exam_due <= today + timedelta(days=cls.WARNING_DAYS):
            days_remaining = (latest_physical.next_exam_due - today).days
            
            if days_remaining <= cls.URGENT_DAYS:
                priority = NotificationPriority.URGENT
                subject = 'URGENT: Medical Physical Due Soon'
            else:
                priority = NotificationPriority.HIGH
                subject = 'Medical Physical Due Soon'
            
            alerts_sent += cls._send_alert(
                member,
                'PHYSICAL',
                subject,
                f'Your medical physical is due in {days_remaining} days ({latest_physical.next_exam_due}). Please schedule your appointment.',
                priority=priority,
                related_id=latest_physical.pk
            )
        
        return alerts_sent
    
    @classmethod
    def check_member_fit_tests(cls, member):
        """Check if member's fit test is expiring or overdue"""
        alerts_sent = 0
        today = timezone.now().date()
        
        # Get most recent passing fit test
        latest_fit_test = FitTest.objects.filter(
            user=member,
            result='PASS'
        ).order_by('-test_date').first()
        
        if not latest_fit_test:
            # No fit test on file
            alerts_sent += cls._send_alert(
                member,
                'FIT_TEST',
                'Fit Test Required',
                'You do not have a current fit test on file. You cannot use SCBA until fit tested.',
                priority=NotificationPriority.HIGH
            )
            return alerts_sent
        
        # Check if expired
        if latest_fit_test.expiration_date < today:
            days_overdue = (today - latest_fit_test.expiration_date).days
            alerts_sent += cls._send_alert(
                member,
                'FIT_TEST',
                'Fit Test EXPIRED',
                f'Your fit test expired {days_overdue} days ago. You cannot use SCBA until re-tested.',
                priority=NotificationPriority.URGENT,
                related_id=latest_fit_test.pk
            )
        
        # Check if expiring soon
        elif latest_fit_test.expiration_date <= today + timedelta(days=cls.WARNING_DAYS):
            days_remaining = (latest_fit_test.expiration_date - today).days
            alerts_sent += cls._send_alert(
                member,
                'FIT_TEST',
                'Fit Test Expiring Soon',
                f'Your fit test expires in {days_remaining} days ({latest_fit_test.expiration_date}). Please schedule your test.',
                priority=NotificationPriority.MEDIUM,
                related_id=latest_fit_test.pk
            )
        
        return alerts_sent
    
    @classmethod
    def check_member_immunizations(cls, member):
        """Check if member has any immunizations due"""
        alerts_sent = 0
        today = timezone.now().date()
        warning_date = today + timedelta(days=cls.WARNING_DAYS)
        
        # Get immunizations with upcoming due dates
        due_immunizations = Immunization.objects.filter(
            user=member,
            next_dose_due__isnull=False,
            next_dose_due__lte=warning_date
        ).order_by('next_dose_due')
        
        for immunization in due_immunizations:
            if immunization.next_dose_due < today:
                # Overdue
                days_overdue = (today - immunization.next_dose_due).days
                alerts_sent += cls._send_alert(
                    member,
                    'IMMUNIZATION',
                    f'{immunization.get_vaccine_type_display()} Overdue',
                    f'Your {immunization.get_vaccine_type_display()} booster is {days_overdue} days overdue.',
                    priority=NotificationPriority.MEDIUM,
                    related_id=immunization.pk
                )
            else:
                # Due soon
                days_remaining = (immunization.next_dose_due - today).days
                alerts_sent += cls._send_alert(
                    member,
                    'IMMUNIZATION',
                    f'{immunization.get_vaccine_type_display()} Due Soon',
                    f'Your {immunization.get_vaccine_type_display()} booster is due in {days_remaining} days.',
                    priority=NotificationPriority.LOW,
                    related_id=immunization.pk
                )
        
        return alerts_sent
    
    @classmethod
    def _send_alert(cls, member, alert_type, subject, message, priority=NotificationPriority.MEDIUM, related_id=None):
        """
        Send an alert to a member and create a ComplianceAlert record
        
        Returns:
            int: 1 if alert sent, 0 if duplicate alert was recently sent
        """
        # Check if we've already sent this alert recently (within 7 days)
        recent_alert = ComplianceAlert.objects.filter(
            user=member,
            alert_type=alert_type,
            sent_at__gte=timezone.now() - timedelta(days=7)
        ).first()
        
        if recent_alert:
            logger.debug(f"Skipping duplicate alert for {member.get_full_name()} - {alert_type}")
            return 0
        
        # Send notification
        success = NotificationManager.send_notification(
            notification_type=NotificationType.CERTIFICATION_EXPIRING,  # Could create specific types
            recipients=[member],
            subject=subject,
            message=message,
            priority=priority,
            context={
                'alert_type': alert_type,
                'related_id': related_id
            }
        )
        
        # Create alert record
        alert = ComplianceAlert.objects.create(
            user=member,
            alert_type=alert_type,
            subject=subject,
            message=message,
            related_object_id=related_id,
            email_delivered=success
        )
        
        # Escalate to supervisor if urgent and overdue
        if priority == NotificationPriority.URGENT:
            cls._escalate_alert(alert)
        
        return 1 if success else 0
    
    @classmethod
    def _escalate_alert(cls, alert):
        """
        Escalate an urgent alert to supervisors/compliance officers
        """
        # Get compliance officers and chief officers
        from django.contrib.auth.models import Group
        
        compliance_officers = User.objects.filter(
            groups__name__in=['Compliance Officers', 'Chief Officers'],
            is_active=True
        ).distinct()
        
        if not compliance_officers:
            return
        
        subject = f"ESCALATED: {alert.subject} - {alert.user.get_full_name()}"
        message = (
            f"The following compliance alert has been escalated:\n\n"
            f"Member: {alert.user.get_full_name()}\n"
            f"Alert Type: {alert.get_alert_type_display()}\n"
            f"Original Message: {alert.message}\n\n"
            f"Please follow up with the member immediately."
        )
        
        NotificationManager.send_notification(
            notification_type=NotificationType.APPROVAL_NEEDED,
            recipients=list(compliance_officers),
            subject=subject,
            message=message,
            priority=NotificationPriority.URGENT
        )
        
        alert.is_escalated = True
        alert.escalation_date = timezone.now()
        alert.save()
    
    @classmethod
    def get_department_compliance_summary(cls):
        """
        Generate a summary report of department-wide compliance status
        
        Returns:
            dict with compliance statistics
        """
        active_members = User.objects.filter(is_active=True)
        today = timezone.now().date()
        
        summary = {
            'total_members': active_members.count(),
            'physicals': {
                'current': 0,
                'expiring_soon': 0,
                'overdue': 0,
                'missing': 0
            },
            'fit_tests': {
                'current': 0,
                'expiring_soon': 0,
                'expired': 0,
                'missing': 0
            },
            'overall_compliance_rate': 0
        }
        
        compliant_count = 0
        
        for member in active_members:
            # Check physical
            physical = MedicalPhysical.objects.filter(
                user=member,
                result__in=['CLEARED', 'CLEARED_WITH_RESTRICTIONS']
            ).order_by('-exam_date').first()
            
            if not physical:
                summary['physicals']['missing'] += 1
            elif physical.next_exam_due < today:
                summary['physicals']['overdue'] += 1
            elif physical.next_exam_due <= today + timedelta(days=30):
                summary['physicals']['expiring_soon'] += 1
                compliant_count += 0.5  # Partial compliance
            else:
                summary['physicals']['current'] += 1
                compliant_count += 1
            
            # Check fit test
            fit_test = FitTest.objects.filter(
                user=member,
                result='PASS'
            ).order_by('-test_date').first()
            
            if not fit_test:
                summary['fit_tests']['missing'] += 1
            elif fit_test.expiration_date < today:
                summary['fit_tests']['expired'] += 1
            elif fit_test.expiration_date <= today + timedelta(days=30):
                summary['fit_tests']['expiring_soon'] += 1
            else:
                summary['fit_tests']['current'] += 1
        
        # Calculate overall compliance rate
        max_compliance = summary['total_members'] * 2  # 2 items per member (physical + fit test)
        if max_compliance > 0:
            summary['overall_compliance_rate'] = (compliant_count / max_compliance) * 100
        
        return summary
