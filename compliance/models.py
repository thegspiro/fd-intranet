from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# --- Model 1: HistoricalShiftRecord ---

class HistoricalShiftRecord(models.Model):
    """
    Archives completed shifts for historical reference and reporting
    """
    # Original shift info
    shift_date = models.DateField(db_index=True)
    shift_template_name = models.CharField(max_length=100, help_text="Name of the shift template used")
    
    # Times
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    # Staffing snapshot (JSON for flexibility)
    roster = models.JSONField(
        default=dict,
        help_text="JSON snapshot of who filled which positions"
    )
    
    # Staffing metrics
    total_positions = models.IntegerField(default=0)
    filled_positions = models.IntegerField(default=0)
    was_fully_staffed = models.BooleanField(default=False)
    
    # Activity during shift
    calls_responded = models.IntegerField(default=0, help_text="Number of calls responded to")
    training_conducted = models.BooleanField(default=False)
    
    # Notes
    shift_notes = models.TextField(blank=True, help_text="Notes about this shift")
    significant_events = models.TextField(
        blank=True,
        help_text="Any significant events or incidents"
    )
    
    # Officer in charge
    officer_in_charge = models.CharField(max_length=200, blank=True)
    
    # Archived metadata
    archived_at = models.DateTimeField(auto_now_add=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shifts_archived'
    )
    
    # Link to original shift (if still exists)
    original_shift_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-shift_date']
        indexes = [
            models.Index(fields=['shift_date']),
            models.Index(fields=['shift_template_name']),
        ]
    
    def __str__(self):
        return f"{self.shift_template_name} - {self.shift_date}"


# --- Model 2: LegacyMemberData ---

class LegacyMemberData(models.Model):
    """
    Stores historical member records for retired/former members
    """
    # Basic info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    badge_number = models.CharField(max_length=20, db_index=True)
    
    # Service dates
    hire_date = models.DateField(null=True, blank=True)
    separation_date = models.DateField(null=True, blank=True, help_text="Date member left department")
    
    # Separation details
    SEPARATION_TYPES = [
        ('RETIRED', 'Retired'),
        ('RESIGNED', 'Resigned'),
        ('TERMINATED', 'Terminated'),
        ('DECEASED', 'Deceased'),
        ('TRANSFERRED', 'Transferred to Another Agency'),
        ('OTHER', 'Other'),
    ]
    separation_type = models.CharField(max_length=20, choices=SEPARATION_TYPES, blank=True)
    separation_reason = models.TextField(blank=True)
    
    # Service summary
    years_of_service = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    highest_rank = models.CharField(max_length=100, blank=True)
    
    # Legacy data snapshot (JSON for flexibility)
    certification_history = models.JSONField(
        default=list,
        help_text="Historical certifications held"
    )
    training_history = models.JSONField(
        default=list,
        help_text="Historical training records"
    )
    awards_commendations = models.JSONField(
        default=list,
        help_text="Awards and commendations received"
    )
    
    # Contact info (if staying in touch)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    mailing_address = models.TextField(blank=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="General notes about member's service")
    
    # Photo
    photo = models.ImageField(upload_to='legacy_photos/', null=True, blank=True)
    
    # Archive metadata
    archived_at = models.DateTimeField(auto_now_add=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='legacy_members_archived'
    )
    
    # Link to original user account (if converted from active user)
    original_user_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['badge_number']),
            models.Index(fields=['separation_date']),
        ]
        verbose_name_plural = 'Legacy Member Data'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (Badge #{self.badge_number})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# --- Model 3: IncidentArchive ---

class IncidentArchive(models.Model):
    """
    Archives incident reports and call data
    """
    # Incident identification
    incident_number = models.CharField(max_length=50, unique=True, db_index=True)
    incident_date = models.DateField(db_index=True)
    incident_time = models.TimeField()
    
    # Type
    INCIDENT_TYPES = [
        ('FIRE', 'Fire'),
        ('EMS', 'EMS/Medical'),
        ('MVA', 'Motor Vehicle Accident'),
        ('HAZMAT', 'Hazardous Materials'),
        ('RESCUE', 'Technical Rescue'),
        ('SERVICE', 'Service Call'),
        ('FALSE_ALARM', 'False Alarm'),
        ('MUTUAL_AID', 'Mutual Aid'),
        ('TRAINING', 'Training'),
        ('OTHER', 'Other'),
    ]
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    
    # Location
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Response details
    dispatch_time = models.DateTimeField(null=True, blank=True)
    enroute_time = models.DateTimeField(null=True, blank=True)
    onscene_time = models.DateTimeField(null=True, blank=True)
    clear_time = models.DateTimeField(null=True, blank=True)
    
    # Units responded (JSON array)
    units_responded = models.JSONField(
        default=list,
        help_text="List of units that responded"
    )
    
    # Personnel (JSON array)
    personnel = models.JSONField(
        default=list,
        help_text="List of personnel who responded"
    )
    
    # Incident commander
    incident_commander = models.CharField(max_length=200, blank=True)
    
    # Description
    description = models.TextField(help_text="Incident description/narrative")
    
    # Actions taken
    actions_taken = models.TextField(blank=True)
    
    # Outcomes
    patient_transported = models.BooleanField(default=False)
    transport_destination = models.CharField(max_length=200, blank=True)
    property_damage = models.BooleanField(default=False)
    injuries = models.BooleanField(default=False)
    fatalities = models.BooleanField(default=False)
    
    # Documentation
    incident_report = models.FileField(
        upload_to='archives/incidents/',
        null=True,
        blank=True
    )
    
    # Archive metadata
    archived_at = models.DateTimeField(auto_now_add=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='incidents_archived'
    )
    
    class Meta:
        ordering = ['-incident_date', '-incident_time']
        indexes = [
            models.Index(fields=['incident_date']),
            models.Index(fields=['incident_type']),
            models.Index(fields=['incident_number']),
        ]
    
    def __str__(self):
        return f"{self.incident_number} - {self.incident_date} ({self.get_incident_type_display()})"


# --- Model 4: AnnualReport ---

class AnnualReport(models.Model):
    """
    Stores annual department summary reports
    """
    year = models.IntegerField(unique=True, db_index=True)
    
    # Response statistics
    total_calls = models.IntegerField(default=0)
    fire_calls = models.IntegerField(default=0)
    ems_calls = models.IntegerField(default=0)
    mva_calls = models.IntegerField(default=0)
    service_calls = models.IntegerField(default=0)
    false_alarms = models.IntegerField(default=0)
    mutual_aid_given = models.IntegerField(default=0)
    mutual_aid_received = models.IntegerField(default=0)
    
    # Response times (minutes, averages)
    avg_response_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    avg_turnout_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Personnel statistics
    total_members = models.IntegerField(default=0)
    active_firefighters = models.IntegerField(default=0)
    probationary_members = models.IntegerField(default=0)
    officers = models.IntegerField(default=0)
    new_members = models.IntegerField(default=0, help_text="New members hired this year")
    separated_members = models.IntegerField(default=0, help_text="Members who left this year")
    
    # Training statistics
    total_training_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    training_sessions_held = models.IntegerField(default=0)
    certifications_earned = models.IntegerField(default=0)
    
    # Equipment/apparatus statistics
    apparatus_count = models.IntegerField(default=0)
    apparatus_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Financial (if tracked)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fundraising_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Narrative sections
    chief_message = models.TextField(blank=True, help_text="Message from the Chief")
    highlights = models.TextField(blank=True, help_text="Major highlights and achievements")
    challenges = models.TextField(blank=True, help_text="Challenges faced")
    goals_next_year = models.TextField(blank=True, help_text="Goals for next year")
    
    # Report document
    report_document = models.FileField(
        upload_to='archives/annual_reports/',
        null=True,
        blank=True,
        help_text="Upload final formatted report (PDF)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='annual_reports_created'
    )
    finalized = models.BooleanField(default=False)
    finalized_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-year']
    
    def __str__(self):
        return f"Annual Report {self.year}"


# --- Model 5: EquipmentHistory ---

class EquipmentHistory(models.Model):
    """
    Tracks historical equipment/apparatus lifecycle
    """
    # Equipment identification
    equipment_name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=100, help_text="Engine, Ladder, Rescue, etc.")
    unit_number = models.CharField(max_length=50, blank=True)
    
    # Acquisition
    acquisition_date = models.DateField(null=True, blank=True)
    acquisition_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    model = models.CharField(max_length=200, blank=True)
    year = models.IntegerField(null=True, blank=True, help_text="Model year")
    vin_serial = models.CharField(max_length=100, blank=True)
    
    # Service history
    in_service_date = models.DateField(null=True, blank=True)
    out_of_service_date = models.DateField(null=True, blank=True)
    years_in_service = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    
    # Disposition
    DISPOSITION_TYPES = [
        ('IN_SERVICE', 'Currently In Service'),
        ('RESERVE', 'Placed in Reserve'),
        ('SOLD', 'Sold'),
        ('SCRAPPED', 'Scrapped'),
        ('TRADED', 'Traded In'),
        ('DONATED', 'Donated'),
        ('DESTROYED', 'Destroyed'),
    ]
    disposition = models.CharField(max_length=20, choices=DISPOSITION_TYPES, default='IN_SERVICE')
    disposition_date = models.DateField(null=True, blank=True)
    disposition_notes = models.TextField(blank=True)
    
    # Service statistics
    total_miles = models.IntegerField(null=True, blank=True)
    total_engine_hours = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
    total_calls_responded = models.IntegerField(null=True, blank=True)
    
    # Notable events
    significant_events = models.TextField(
        blank=True,
        help_text="Major repairs, accidents, notable incidents"
    )
    
    # Photos
    photo = models.ImageField(upload_to='archives/equipment/', null=True, blank=True)
    
    # Documentation
    documentation = models.FileField(
        upload_to='archives/equipment_docs/',
        null=True,
        blank=True
    )
    
    # Metadata
    archived_at = models.DateTimeField(auto_now_add=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='equipment_archived'
    )
    
    class Meta:
        ordering = ['-in_service_date']
        verbose_name_plural = 'Equipment History'
    
    def __str__(self):
        return f"{self.equipment_name} ({self.equipment_type})"
