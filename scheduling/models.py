from django.db import models
from django.contrib.auth.models import User
from accounts.models import CertificationStandard

# --- Model 1: Position ---

class Position(models.Model):
    """
    Defines a required role on a shift (e.g., Captain, Driver, Primary EMT).
    Positions are created by the load_initial_data command.
    """
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True, help_text="Short code for display (e.g., CAPT, DRVR).")
    
    # Links to the CertificationStandard model to enforce qualifications
    required_certification = models.ForeignKey(
        CertificationStandard, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Certification required to fill this position."
    )

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['code']


# --- Model 2: ShiftTemplate ---

class ShiftTemplate(models.Model):
    """
    Defines the standard recurring structure of a shift (e.g., 24-hour shift, 
    Duty Crew, etc.) which is used to generate actual Shift instances.
    """
    name = models.CharField(max_length=100, unique=True)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, help_text="Duration of the shift in hours (e.g., 24.00, 12.00).")
    start_time = models.TimeField(help_text="The standard starting time (e.g., 07:00:00).")
    
    # Defines the minimum staffing requirements for this template
    minimum_staff = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['start_time']


# --- Model 3: ShiftSlotTemplate ---

class ShiftSlotTemplate(models.Model):
    """
    Defines the specific positions needed for a ShiftTemplate.
    e.g., A '24-hour shift' template requires 1 CAPT and 2 EMT1s.
    """
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.CASCADE, related_name='slots')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    count = models.IntegerField(default=1, help_text="Number of people required for this position on the shift.")

    def __str__(self):
        return f"{self.shift_template.name}: {self.count} x {self.position.code}"
    
    class Meta:
        # Ensures a template doesn't accidentally define the same position twice
        unique_together = ('shift_template', 'position')


# --- Model 4: Shift (The actual scheduled event) ---

class Shift(
