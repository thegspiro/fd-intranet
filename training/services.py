"""
Training Services - Now platform-agnostic
"""
import logging
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from .models import TrainingRequirement, TrainingRecord
from integrations.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


class TrainingService:
    """Platform-agnostic training management service"""
    
    def __init__(self):
        # Get configured training provider dynamically
        self.provider = IntegrationRegistry.get_training_provider()
        if not self.provider:
            logger.warning("No training provider configured")
    
    def sync_member_records(self, member, external_id: str) -> int:
        """
        Sync training records from configured provider
        Works with ANY training provider that implements the adapter
        """
        if not self.provider:
            logger.error("Cannot sync: no training provider configured")
            return 0
        
        try:
            # Fetch from provider (works with Target Solutions, Skillsoft, etc.)
            standard_records = self.provider.get_member_records(external_id)
            
            synced_count = 0
            for record in standard_records:
                # Store in local database
                obj, created = TrainingRecord.objects.update_or_create(
                    member=member,
                    provider_record_id=record.provider_record_id,
                    provider=record.provider,
                    defaults={
                        'course_name': record.course_name,
                        'completion_date': record.completion_date,
                        'expiration_date': record.expiration_date,
                        'score': record.score,
                        'status': record.status,
                        'certificate_id': record.certificate_id,
                        'instructor': record.instructor,
                        'metadata': record.metadata or {}
                    }
                )
                
                if created:
                    synced_count += 1
                    logger.info(f"Created new training record: {record.course_name}")
            
            return synced_count
        
        except Exception as e:
            logger.error(f"Failed to sync training records: {e}")
            return 0
    
    def get_member_compliance_status(self, member) -> dict:
        """Calculate compliance status for member"""
        requirements = TrainingRequirement.objects.filter(
            required_for_ranks__in=[member.rank]
        )
        
        total = requirements.count()
        completed = 0
        expired = 0
        upcoming = 0
        
        for req in requirements:
            record = TrainingRecord.objects.filter(
                member=member,
                course_name=req.course_name,
                status='completed'
            ).order_by('-completion_date').first()
            
            if record:
                if record.expiration_date:
                    if record.expiration_date < datetime.now().date():
                        expired += 1
                    elif (record.expiration_date - datetime.now().date()).days < 30:
                        upcoming += 1
                        completed += 1
                    else:
                        completed += 1
                else:
                    completed += 1
        
        compliance_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'total_requirements': total,
            'completed': completed,
            'expired': expired,
            'upcoming_expiration': upcoming,
            'compliance_rate': round(compliance_rate, 1)
        }
    
    def enroll_in_course(self, member, course_id: str, external_member_id: str) -> bool:
        """Enroll member in course through provider"""
        if not self.provider:
            logger.error("Cannot enroll: no training provider configured")
            return False
        
        try:
            return self.provider.enroll_member(external_member_id, course_id)
        except Exception as e:
            logger.error(f"Failed to enroll member: {e}")
            return False
