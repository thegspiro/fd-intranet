from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone


# --- Model 1: UserProfile ---

class UserProfile(models.Model):
    """
    Extended profile information for fire department members
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    
    # Basic Info
    badge_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in format: '+999999999'. Up to 15 digits."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Address
    street_address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    
    # Department Info
    hire_date = models.DateField(null=True, blank=True, help_text="Date member joined the department")
    probation_end_date = models.DateField(null=True, blank=True, help_text="End of probationary period")
    
    # Status
    is_active_duty = models.BooleanField(default=True)
    leave_of_absence = models.BooleanField(default=False)
    leave_start_date = models.DateField(null=True, blank=True)
    leave_end_date = models.DateField(null=True, blank=True)
    leave_reason = models.TextField(blank=True)
    
    # Profile photo
    photo = models.ImageField(upload_to='member_photos/', null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Internal notes about this member")
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Badge #{self.badge_number}"
    
    @property
    def is_probationary(self):
        """Check if member is still in probationary period"""
        if self.probation_end_date:
            return self.probation_end_date > timezone.now().date()
        return False
    
    class Meta:
        ordering = ['badge_number']


# --- Model 2: CertificationStandard ---

class CertificationStandard(models.Model):
    """
    Defines the types of certifications members can hold
    (e.g., FF1, FF2, EMT-B, Driver/Operator)
    """
    name = models.CharField(max_length=100, unique=True, help_text="Full name of certification")
    abbreviation = models.CharField(max_length=20, help_text="Short code (e.g., FF1, EMT-B)")
    description = models.TextField(blank=True)
    
    # Validity
    requires_expiration = models.BooleanField(
        default=True,
        help_text="Does this certification expire?"
    )
    validity_years = models.IntegerField(
        null=True,
        blank=True,
        help_text="How many years is this certification valid?"
    )
    
    # Ordering/hierarchy
    level = models.IntegerField(
        default=1,
        help_text="Level/rank of this certification (1=basic, higher=advanced)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
    
    class Meta:
        ordering = ['level', 'name']


# --- Model 3: MemberCertification ---

class MemberCertification(models.Model):
    """
    Tracks individual certifications held by members
    """
    VERIFICATION_STATUS = [
        ('PENDING', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    standard = models.ForeignKey(CertificationStandard, on_delete=models.CASCADE)
    
    # Dates
    issue_date = models.DateField(help_text="Date certification was issued")
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date certification expires (if applicable)"
    )
    
    # Documentation
    certificate_number = models.CharField(max_length=100, blank=True)
    issuing_agency = models.CharField(max_length=200, blank=True, help_text="Who issued this certification")
    document = models.FileField(
        upload_to='certifications/',
        null=True,
        blank=True,
        help_text="Upload certificate or proof of certification"
    )
    
    # Verification
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='PENDING')
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certifications_verified',
        help_text="Officer who verified this certification"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.standard.name} ({self.verification_status})"
    
    @property
    def is_expired(self):
        """Check if certification has expired"""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False
    
    @property
    def days_until_expiration(self):
        """Calculate days remaining until expiration"""
        if self.expiration_date:
            delta = self.expiration_date - timezone.now().date()
            return delta.days
        return None
    
    def save(self, *args, **kwargs):
        # Auto-mark as expired if expiration date has passed
        if self.is_expired and self.verification_status == 'APPROVED':
            self.verification_status = 'EXPIRED'
        
        # Set verified_at timestamp when status changes to APPROVED
        if self.verification_status == 'APPROVED' and not self.verified_at:
            self.verified_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-issue_date']
        unique_together = ('user', 'standard', 'issue_date')  # Prevent duplicate entries


# --- Model 4: DataChangeRequest ---

class DataChangeRequest(models.Model):
    """
    Members submit requests to change their profile data.
    Secretary reviews and approves/rejects.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_change_requests')
    
    # What field is being changed
    field_name = models.CharField(
        max_length=100,
        help_text="Name of the field being changed (e.g., 'phone_number', 'address')"
    )
    current_value = models.TextField(blank=True, help_text="Current value of the field")
    new_value = models.TextField(help_text="Requested new value")
    
    # Justification
    reason = models.TextField(blank=True, help_text="Why this change is needed")
    
    # Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='data_changes_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    request_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.field_name} ({self.status})"
    
    class Meta:
        ordering = ['-request_date']


# --- Model 5: PersonnelRecord (Sensitive Documents with OLP) ---

class PersonnelRecord(models.Model):
    """
    Stores sensitive personnel documents (annual reviews, disciplinary actions, etc.)
    Uses django-guardian for object-level permissions
    """
    RECORD_TYPES = [
        ('ANNUAL_REVIEW', 'Annual Performance Review'),
        ('DISCIPLINARY', 'Disciplinary Action'),
        ('COMMENDATION', 'Commendation/Award'),
        ('INCIDENT', 'Incident Report'),
        ('MEDICAL', 'Medical Documentation'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personnel_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Document
    document = models.FileField(
        upload_to='personnel_records/',
        help_text="Upload confidential document"
    )
    
    # Dates
    record_date = models.DateField(help_text="Date of the event/review")
    
    # Access control (in addition to guardian OLP)
    is_confidential = models.BooleanField(
        default=True,
        help_text="Restrict access to Chief Officers only"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='personnel_records_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_record_type_display()} ({self.record_date})"
    
    class Meta:
        ordering = ['-record_date']
        permissions = [
            ('view_own_record', 'Can view own personnel record'),
            ('view_all_records', 'Can view all personnel records'),
        ]
