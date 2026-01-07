from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


# --- Model 1: MedicalPhysical ---

class MedicalPhysical(models.Model):
    """
    Tracks annual medical physicals and fitness-for-duty evaluations
    """
    EXAM_TYPES = [
        ('ANNUAL', 'Annual Physical'),
        ('PRE_EMPLOYMENT', 'Pre-Employment Physical'),
        ('RETURN_TO_DUTY', 'Return to Duty'),
        ('FITNESS_FOR_DUTY', 'Fitness for Duty'),
    ]
    
    RESULT_CHOICES = [
        ('CLEARED', 'Cleared for Full Duty'),
        ('CLEARED_WITH_RESTRICTIONS', 'Cleared with Restrictions'),
        ('NOT_CLEARED', 'Not Cleared'),
        ('PENDING', 'Pending Results'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_physicals')
    
    # Exam details
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='ANNUAL')
    exam_date = models.DateField(help_text="Date physical was conducted")
    next_exam_due = models.DateField(help_text="When next physical is due")
    
    # Provider info
    provider_name = models.CharField(max_length=200, blank=True)
    provider_facility = models.CharField(max_length=200, blank=True)
    
    # Results
    result = models.CharField(max_length=30, choices=RESULT_CHOICES, default='PENDING')
    restrictions = models.TextField(
        blank=True,
        help_text="Any duty restrictions or limitations"
    )
    
    # Vital signs
    height_inches = models.IntegerField(null=True, blank=True)
    weight_pounds = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, blank=True, help_text="e.g., 120/80")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Beats per minute")
    
    # Documentation
    documentation = models.FileField(
        upload_to='medical/physicals/',
        null=True,
        blank=True,
        help_text="Upload physical exam report"
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Additional notes or findings")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='physicals_recorded'
    )
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_exam_type_display()} ({self.exam_date})"
    
    @property
    def is_overdue(self):
        """Check if next exam is overdue"""
        return self.next_exam_due < timezone.now().date()
    
    @property
    def days_until_due(self):
        """Calculate days until next exam is due"""
        delta = self.next_exam_due - timezone.now().date()
        return delta.days
    
    class Meta:
        ordering = ['-exam_date']
        verbose_name_plural = 'Medical Physicals'


# --- Model 2: FitTest ---

class FitTest(models.Model):
    """
    Tracks respiratory fit testing for SCBA/respirator use
    """
    TEST_TYPES = [
        ('QUALITATIVE', 'Qualitative (Taste/Smell Test)'),
        ('QUANTITATIVE', 'Quantitative (PortaCount)'),
    ]
    
    RESULT_CHOICES = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fit_tests')
    
    # Test details
    test_date = models.DateField(default=timezone.now)
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    
    # Equipment tested
    mask_manufacturer = models.CharField(max_length=100, help_text="e.g., Scott, MSA, Honeywell")
    mask_model = models.CharField(max_length=100, help_text="e.g., AV-3000, M7")
    mask_size = models.CharField(max_length=20, help_text="e.g., Small, Medium, Large")
    
    # Quantitative results
    fit_factor = models.IntegerField(
        null=True,
        blank=True,
        help_text="Overall fit factor (quantitative tests only)"
    )
    
    # Tester info
    tester = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fit_tests_conducted',
        help_text="Who conducted the fit test"
    )
    
    # Validity
    expiration_date = models.DateField(help_text="Annual fit test required")
    
    # Documentation
    test_report = models.FileField(
        upload_to='medical/fit_tests/',
        null=True,
        blank=True,
        help_text="Upload fit test report"
    )
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Fit Test {self.test_date} ({self.result})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate expiration (1 year from test date)
        if not self.expiration_date:
            self.expiration_date = self.test_date + timedelta(days=365)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if fit test has expired"""
        return self.expiration_date < timezone.now().date()
    
    class Meta:
        ordering = ['-test_date']


# --- Model 3: Immunization ---

class Immunization(models.Model):
    """
    Tracks immunizations and vaccinations
    """
    VACCINE_TYPES = [
        ('HEPATITIS_A', 'Hepatitis A'),
        ('HEPATITIS_B', 'Hepatitis B'),
        ('TETANUS', 'Tetanus/Tdap'),
        ('MMR', 'MMR (Measles, Mumps, Rubella)'),
        ('VARICELLA', 'Varicella (Chickenpox)'),
        ('INFLUENZA', 'Influenza (Annual Flu)'),
        ('COVID19', 'COVID-19'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='immunizations')
    
    # Vaccine details
    vaccine_type = models.CharField(max_length=20, choices=VACCINE_TYPES)
    vaccine_name = models.CharField(max_length=200, blank=True, help_text="Specific vaccine product name")
    
    # Administration
    administration_date = models.DateField()
    dose_number = models.IntegerField(default=1, help_text="Which dose in the series (e.g., 1 of 2)")
    total_doses = models.IntegerField(default=1, help_text="Total doses in series")
    
    # Provider
    administered_by = models.CharField(max_length=200, blank=True, help_text="Healthcare provider")
    facility = models.CharField(max_length=200, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    
    # Expiration/next dose
    expiration_date = models.DateField(null=True, blank=True, help_text="When this immunity expires")
    next_dose_due = models.DateField(null=True, blank=True, help_text="When next dose/booster is due")
    
    # Documentation
    documentation = models.FileField(
        upload_to='medical/immunizations/',
        null=True,
        blank=True,
        help_text="Upload vaccination record"
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_vaccine_type_display()} ({self.administration_date})"
    
    @property
    def is_series_complete(self):
        """Check if vaccination series is complete"""
        return self.dose_number >= self.total_doses
    
    class Meta:
        ordering = ['-administration_date']


# --- Model 4: OSHA_Log ---

class OSHALog(models.Model):
    """
    OSHA 300 Log - Workplace injury and illness tracking
    """
    INCIDENT_TYPES = [
        ('INJURY', 'Injury'),
        ('ILLNESS', 'Illness'),
        ('EXPOSURE', 'Exposure Incident'),
    ]
    
    SEVERITY_LEVELS = [
        ('FIRST_AID', 'First Aid Only'),
        ('MEDICAL_TREATMENT', 'Medical Treatment'),
        ('RESTRICTED_WORK', 'Restricted Work Activity'),
        ('LOST_TIME', 'Days Away from Work'),
        ('FATALITY', 'Fatality'),
    ]
    
    # Employee info
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='osha_incidents')
    
    # Incident details
    incident_date = models.DateField(help_text="Date of injury/illness")
    incident_time = models.TimeField(null=True, blank=True)
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES)
    
    # Location
    location = models.CharField(max_length=200, help_text="Where did the incident occur?")
    
    # Description
    description = models.TextField(help_text="Describe what happened")
    body_part = models.CharField(max_length=100, blank=True, help_text="Affected body part")
    injury_nature = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nature of injury (cut, burn, fracture, etc.)"
    )
    
    # Classification
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    is_recordable = models.BooleanField(
        default=True,
        help_text="Is this recordable under OSHA 300 requirements?"
    )
    
    # Work status
    days_away_from_work = models.IntegerField(default=0)
    days_on_restricted_duty = models.IntegerField(default=0)
    return_to_work_date = models.DateField(null=True, blank=True)
    
    # Medical treatment
    treatment_facility = models.CharField(max_length=200, blank=True)
    treating_physician = models.CharField(max_length=200, blank=True)
    
    # Privacy case
    is_privacy_case = models.BooleanField(
        default=False,
        help_text="Check if case involves privacy concerns (HIV, mental health, etc.)"
    )
    
    # Root cause
    contributing_factors = models.TextField(
        blank=True,
        help_text="What factors contributed to this incident?"
    )
    corrective_actions = models.TextField(
        blank=True,
        help_text="What actions were taken to prevent recurrence?"
    )
    
    # Documentation
    incident_report = models.FileField(
        upload_to='compliance/osha_logs/',
        null=True,
        blank=True,
        help_text="Upload incident report"
    )
    
    # Metadata
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='osha_incidents_reported'
    )
    reported_date = models.DateTimeField(auto_now_add=True)
    
    # Case number (OSHA 300 Log)
    case_number = models.CharField(max_length=20, unique=True, blank=True)
    
    def __str__(self):
        return f"OSHA {self.case_number} - {self.employee.get_full_name()} ({self.incident_date})"
    
    def save(self, *args, **kwargs):
        # Auto-generate case number if not set
        if not self.case_number:
            year = self.incident_date.year
            count = OSHALog.objects.filter(incident_date__year=year).count() + 1
            self.case_number = f"{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-incident_date']
        verbose_name = 'OSHA Log Entry'
        verbose_name_plural = 'OSHA Log Entries'


# --- Model 5: ExposureIncident ---

class ExposureIncident(models.Model):
    """
    Tracks exposure incidents requiring medical follow-up
    (bloodborne pathogens, hazmat, etc.)
    """
    EXPOSURE_TYPES = [
        ('BLOODBORNE', 'Bloodborne Pathogen'),
        ('HAZMAT', 'Hazardous Material'),
        ('SMOKE', 'Smoke/Toxic Inhalation'),
        ('RADIATION', 'Radiation'),
        ('BIOLOGICAL', 'Biological Agent'),
        ('OTHER', 'Other'),
    ]
    
    ROUTE_OF_EXPOSURE = [
        ('PERCUTANEOUS', 'Percutaneous (Needle/Sharp)'),
        ('MUCOUS_MEMBRANE', 'Mucous Membrane (Eye/Mouth)'),
        ('INHALATION', 'Inhalation'),
        ('SKIN_CONTACT', 'Skin Contact'),
        ('INGESTION', 'Ingestion'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exposure_incidents')
    
    # Incident details
    exposure_date = models.DateField()
    exposure_time = models.TimeField(null=True, blank=True)
    exposure_type = models.CharField(max_length=20, choices=EXPOSURE_TYPES)
    route_of_exposure = models.CharField(max_length=20, choices=ROUTE_OF_EXPOSURE)
    
    # Source
    source_description = models.TextField(help_text="Describe the source of exposure")
    incident_location = models.CharField(max_length=200)
    
    # Immediate response
    decontamination_performed = models.BooleanField(default=False)
    decontamination_details = models.TextField(blank=True)
    ppe_worn = models.TextField(blank=True, help_text="What PPE was being worn?")
    
    # Medical follow-up
    immediate_medical_care = models.BooleanField(default=False)
    medical_facility = models.CharField(max_length=200, blank=True)
    treating_physician = models.CharField(max_length=200, blank=True)
    
    # Testing/prophylaxis
    baseline_testing_done = models.BooleanField(default=False)
    baseline_testing_date = models.DateField(null=True, blank=True)
    prophylaxis_offered = models.BooleanField(default=False)
    prophylaxis_accepted = models.BooleanField(default=False)
    
    # Follow-up schedule
    follow_up_required = models.BooleanField(default=True)
    next_follow_up_date = models.DateField(null=True, blank=True)
    follow_up_complete = models.BooleanField(default=False)
    
    # Documentation
    incident_report = models.FileField(
        upload_to='compliance/exposures/',
        null=True,
        blank=True
    )
    
    # Linked OSHA log
    osha_log = models.OneToOneField(
        OSHALog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exposure_detail'
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_exposure_type_display()} ({self.exposure_date})"
    
    class Meta:
        ordering = ['-exposure_date']


# --- Model 6: ComplianceAlert ---

class ComplianceAlert(models.Model):
    """
    Tracks alerts sent to members about expiring compliance items
    """
    ALERT_TYPES = [
        ('PHYSICAL', 'Medical Physical Due'),
        ('FIT_TEST', 'Fit Test Expiring'),
        ('IMMUNIZATION', 'Immunization Due'),
        ('CERTIFICATION', 'Certification Expiring'),
        ('TRAINING', 'Training Required'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compliance_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    
    # Alert content
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related item
    related_object_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of the related compliance item"
    )
    
    # Delivery
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_via_email = models.BooleanField(default=True)
    email_delivered = models.BooleanField(default=False)
    
    # Acknowledgment
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Escalation
    is_escalated = models.BooleanField(default=False, help_text="Alert escalated to supervisor")
    escalation_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_alert_type_display()}"
    
    class Meta:
        ordering = ['-sent_at']
