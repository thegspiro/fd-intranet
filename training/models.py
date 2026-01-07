from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import CertificationStandard


# --- Model 1: TrainingRequirement ---

class TrainingRequirement(models.Model):
    """
    Defines a training competency that members must complete.
    Can be initial certification, annual refresher, or skills maintenance.
    """
    REQUIREMENT_TYPES = [
        ('INITIAL', 'Initial Certification'),
        ('ANNUAL', 'Annual Requirement'),
        ('SKILLS', 'Skills Maintenance'),
        ('DRIVER', 'Driver/Operator'),
        ('OFFICER', 'Officer Development'),
    ]
    
    FREQUENCY_CHOICES = [
        ('ONCE', 'One-Time Only'),
        ('ANNUAL', 'Annually'),
        ('BIENNIAL', 'Every 2 Years'),
        ('TRIENNIAL', 'Every 3 Years'),
    ]
    
    name = models.CharField(max_length=200, help_text="Name of the training requirement")
    description = models.TextField(blank=True, help_text="Detailed description of what this training covers")
    requirement_type = models.CharField(max_length=20, choices=REQUIREMENT_TYPES, default='SKILLS')
    
    # Frequency and validity
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='ANNUAL')
    validity_months = models.IntegerField(
        null=True, 
        blank=True,
        help_text="How many months this training remains valid (null for ONCE type)"
    )
    
    # Prerequisites
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        help_text="Other requirements that must be completed first"
    )
    
    # Associated certification standard
    certification_standard = models.ForeignKey(
        CertificationStandard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Certification standard this training fulfills"
    )
    
    # Target Solutions integration
    target_solutions_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Course ID in Target Solutions system"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_requirement_type_display()})"
    
    class Meta:
        ordering = ['requirement_type', 'name']


# --- Model 2: TrainingRecord ---

class TrainingRecord(models.Model):
    """
    Tracks completion of training requirements by individual members.
    """
    VERIFICATION_STATUS = [
        ('PENDING', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_records')
    requirement = models.ForeignKey(TrainingRequirement, on_delete=models.CASCADE, related_name='completion_records')
    
    # Completion details
    completion_date = models.DateField(help_text="Date training was completed")
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date this training expires (auto-calculated or manual)"
    )
    
    # Instructor/verification
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_instructed',
        help_text="Who conducted or verified this training"
    )
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='PENDING')
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_verifications',
        help_text="Training officer who verified completion"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Documentation
    certificate_document = models.FileField(
        upload_to='training/certificates/',
        null=True,
        blank=True,
        help_text="Upload certificate or completion document"
    )
    notes = models.TextField(blank=True, help_text="Additional notes about this training session")
    
    # Hours tracking
    hours_completed = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Number of training hours completed"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.requirement.name} ({self.completion_date})"
    
    def save(self, *args, **kwargs):
        # Auto-set verified_at when verification status changes to APPROVED
        if self.verification_status == 'APPROVED' and not self.verified_at:
            self.verified_at = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-completion_date']


# --- Model 3: PracticalEvaluation ---

class PracticalEvaluation(models.Model):
    """
    Tracks hands-on practical skills evaluations (e.g., driver check-rides, 
    pump operations, rescue techniques).
    """
    EVAL_TYPES = [
        ('DRIVER', 'Driver Evaluation'),
        ('PUMP', 'Pump Operation'),
        ('RESCUE', 'Technical Rescue'),
        ('EMS', 'EMS Skills'),
        ('LADDER', 'Aerial/Ladder Operation'),
        ('OTHER', 'Other Skills'),
    ]
    
    RESULT_CHOICES = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('REMEDIAL', 'Needs Remedial Training'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practical_evaluations')
    evaluation_type = models.CharField(max_length=20, choices=EVAL_TYPES)
    
    # Evaluation details
    evaluation_date = models.DateField()
    evaluator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evaluations_conducted',
        help_text="Officer conducting the evaluation"
    )
    
    # Skills checklist (JSON field for flexibility)
    skills_checklist = models.JSONField(
        default=dict,
        help_text="Structured checklist of skills evaluated"
    )
    
    # Results
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    overall_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Overall percentage score (0-100)"
    )
    
    # Feedback
    strengths = models.TextField(blank=True, help_text="Areas of strength")
    areas_for_improvement = models.TextField(blank=True, help_text="Areas needing improvement")
    remedial_plan = models.TextField(
        blank=True,
        help_text="Plan for remedial training if needed"
    )
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_evaluation_type_display()} ({self.result})"
    
    class Meta:
        ordering = ['-evaluation_date']


# --- Model 4: TrainingSession ---

class TrainingSession(models.Model):
    """
    Represents a scheduled training event where multiple members can participate.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Related requirement (optional)
    requirement = models.ForeignKey(
        TrainingRequirement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    
    # Schedule
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, default="Station 1")
    
    # Instructor
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='training_sessions_taught'
    )
    
    # Capacity
    max_participants = models.IntegerField(default=20, help_text="Maximum number of participants")
    
    # Attendance tracking
    attendees = models.ManyToManyField(
        User,
        through='TrainingAttendance',
        related_name='training_sessions_attended'
    )
    
    # Status
    is_mandatory = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='training_sessions_created'
    )
    
    def __str__(self):
        return f"{self.title} - {self.session_date}"
    
    @property
    def is_full(self):
        return self.attendees.count() >= self.max_participants
    
    class Meta:
        ordering = ['-session_date', 'start_time']


# --- Model 5: TrainingAttendance ---

class TrainingAttendance(models.Model):
    """
    Through model for tracking attendance at training sessions.
    """
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Registration
    registered_at = models.DateTimeField(auto_now_add=True)
    
    # Attendance
    attended = models.BooleanField(default=False)
    attendance_marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_markings'
    )
    attendance_marked_at = models.DateTimeField(null=True, blank=True)
    
    # Performance
    notes = models.TextField(blank=True)
    
    def __str__(self):
        status = "Attended" if self.attended else "Registered"
        return f"{self.user.get_full_name()} - {self.session.title} ({status})"
    
    class Meta:
        unique_together = ('session', 'user')
        ordering = ['session', 'user__last_name']
