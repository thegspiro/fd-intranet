"""
Base adapters for platform-agnostic integrations
All provider implementations must inherit from these base classes
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StandardTrainingRecord:
    """Standardized training record format"""
    member_id: str
    course_name: str
    course_id: str
    completion_date: datetime
    expiration_date: Optional[datetime]
    score: Optional[float]
    status: str  # 'completed', 'in_progress', 'failed', 'expired'
    certificate_id: Optional[str]
    instructor: Optional[str]
    provider: str
    provider_record_id: str
    metadata: Dict[str, Any] = None


@dataclass
class StandardCalendarEvent:
    """Standardized calendar event format"""
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    description: Optional[str]
    attendees: List[str]  # Email addresses
    event_id: Optional[str]
    provider: str
    metadata: Dict[str, Any] = None


class BaseIntegrationAdapter(ABC):
    """Base class for all integration adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._authenticated = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the provider"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status info"""
        pass
    
    def is_authenticated(self) -> bool:
        return self._authenticated


class TrainingProviderAdapter(BaseIntegrationAdapter):
    """Base adapter for training management systems"""
    
    @abstractmethod
    def get_member_records(self, member_id: str) -> List[StandardTrainingRecord]:
        """Fetch all training records for a member"""
        pass
    
    @abstractmethod
    def get_course_catalog(self) -> List[Dict[str, Any]]:
        """Retrieve available courses"""
        pass
    
    @abstractmethod
    def sync_completion(self, record: StandardTrainingRecord) -> bool:
        """Push completion record to provider"""
        pass
    
    @abstractmethod
    def get_certifications(self, member_id: str) -> List[Dict[str, Any]]:
        """Get active certifications for member"""
        pass
    
    @abstractmethod
    def enroll_member(self, member_id: str, course_id: str) -> bool:
        """Enroll member in a course"""
        pass


class CalendarProviderAdapter(BaseIntegrationAdapter):
    """Base adapter for calendar systems"""
    
    @abstractmethod
    def create_event(self, event: StandardCalendarEvent) -> str:
        """Create calendar event, return event ID"""
        pass
    
    @abstractmethod
    def update_event(self, event_id: str, event: StandardCalendarEvent) -> bool:
        """Update existing event"""
        pass
    
    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete calendar event"""
        pass
    
    @abstractmethod
    def get_events(self, start_date: datetime, end_date: datetime) -> List[StandardCalendarEvent]:
        """Retrieve events in date range"""
        pass
    
    @abstractmethod
    def get_event(self, event_id: str) -> Optional[StandardCalendarEvent]:
        """Get single event by ID"""
        pass


class DocumentStorageAdapter(BaseIntegrationAdapter):
    """Base adapter for document storage systems"""
    
    @abstractmethod
    def upload_file(self, file_content: bytes, filename: str, 
                   folder: str, metadata: Dict = None) -> str:
        """Upload file, return file ID"""
        pass
    
    @abstractmethod
    def download_file(self, file_id: str) -> bytes:
        """Download file contents"""
        pass
    
    @abstractmethod
    def list_files(self, folder: str) -> List[Dict[str, Any]]:
        """List files in folder"""
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    def create_folder(self, folder_name: str, parent_folder: str = None) -> str:
        """Create folder, return folder ID"""
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata without downloading"""
        pass


class NotificationAdapter(BaseIntegrationAdapter):
    """Base adapter for notification systems"""
    
    @abstractmethod
    def send_email(self, to: List[str], subject: str, 
                  body: str, html: bool = False) -> bool:
        """Send email notification"""
        pass
    
    @abstractmethod
    def send_sms(self, to: List[str], message: str) -> bool:
        """Send SMS notification"""
        pass
    
    @abstractmethod
    def send_push(self, user_ids: List[str], title: str, message: str) -> bool:
        """Send push notification"""
        pass
