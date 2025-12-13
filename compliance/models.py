from django.db import models
from django.contrib.auth.models import User
from accounts.models import CertificationStandard
from scheduling.models import Position

# --- Choices for SafetyNet Type ---
SAFETY_NET_TYPE_CHOICES = [
    ('MANPOWER', 'Minimum Staffing Level'),
    ('QUALIFICATION', 'Mandatory Position Certification'),
]

# --- Model 1: SafetyStandard ---

class SafetyStandard(models.Model):
    """
    Defines a mandatory department-wide safety or training standard 
    (e.g., Annual ladder training, SCBA fit test).
    These are typically binary (passed/failed).
    """
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_mandatory_annual = models.BooleanField(default=False, help_text="Requires annual renewal/re-verification.")
    
    # Optional link to a CertificationStandard, if passing this standard
    # grants a formal certification (e.g., HAZMAT Awareness)
    linked_certification = models.OneToOneField(
        CertificationStandard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If passing this standard automatically grants a CertificationStandard."
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# --- Model 2: MemberComplianceRecord ---

class MemberComplianceRecord(models.Model):
    """
    Tracks a specific member's status against a SafetyStandard.
    Used by the Compliance Officer to track mandatory training/tests.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    standard = models.ForeignKey(SafetyStandard, on_delete=models.CASCADE)
    
    # Status of compliance
    is_compliant = models.BooleanField(default=False)
    
    # Date the standard was met or last renewed
    date_met = models.DateField()
    
    # Optional fields for non-compliant members
    notes = models.TextField(blank=True)
    
    # Metadata
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verified_compliance')
    date_verified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.standard.name}: {'Compliant' if self.is_compliant else 'Non-Compliant'}"

    class Meta:
        # A member can only have one active record per standard
        unique_together = ('user', 'standard')
        ordering = ['standard__name', 'user__last_name']


# --- Model 3: SafetyNetConfiguration ---

class SafetyNetConfiguration(models.Model):
    """
    Defines department-specific rules that override standard checks 
    or enforce critical safety minimums.
    e.g., "The Primary EMT position MUST be filled by a person with 
    at least 3 years experience."
    """
    name = models.CharField(max_length=150, help_text="A descriptive name for this specific safety rule.")
    type = models.CharField(max_length=15, choices=SAFETY_NET_TYPE_CHOICES)
    
    # The Position this rule applies to (only used for QUALIFICATION type)
    position = models.ForeignKey(
        Position, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="The position this safety net applies to (e.g., Driver)."
    )
    
    # The value to enforce (e.g., '3' for manpower, or a specific CertificationStandard PK for qualification)
    enforcement_value = models.CharField(
        max_length=255, 
        help_text="The minimum number, or the name of the certification/standard to enforce."
    )
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Safety Net: {self.name} ({self.get_type_display()})"
    
    class Meta:
        ordering = ['type', 'name']
