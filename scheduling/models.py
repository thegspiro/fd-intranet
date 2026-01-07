from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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

class Shift(models.Model):
    """
    Represents an actual scheduled shift instance created from a ShiftTemplate.
    Contains the specific date, times, and staffing status.
    """
    date = models.DateField(help_text="The calendar date this shift occurs.")
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.CASCADE, related_name='instances')
    
    # Computed datetime fields for precise scheduling
    start_datetime = models.DateTimeField(help_text="Full start date and time.")
    end_datetime = models.DateTimeField(help_text="Full end date and time.")
    
    # Staffing status
    is_fully_staffed = models.BooleanField(default=False, help_text="True when all slots are filled.")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    # Notes for this specific shift instance
    notes = models.TextField(blank=True, help_text="Special notes for this shift (e.g., training drill, standby event).")

    def __str__(self):
        return f"{self.shift_template.name} on {self.date}"
    
    class Meta:
        ordering = ['date', 'start_datetime']
        unique_together = ('date', 'shift_template')  # Prevent duplicate shifts for same template on same date


# --- Model 5: ShiftSlot (Individual position on a shift) ---

class ShiftSlot(models.Model):
    """
    Represents a single position slot on a Shift that can be filled by a member.
    Created automatically when a Shift is generated from a ShiftTemplate.
    """
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='slots')
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    
    # Assignment tracking
    filled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='shift_assignments')
    is_filled = models.BooleanField(default=False)
    
    # Timestamps for tracking
    filled_at = models.DateTimeField(null=True, blank=True, help_text="When this slot was claimed.")
    
    def __str__(self):
        status = f"Filled by {self.filled_by.get_full_name()}" if self.filled_by else "Open"
        return f"{self.shift} - {self.position.code} ({status})"
    
    def save(self, *args, **kwargs):
        # Auto-set filled_at timestamp when slot is claimed
        if self.filled_by and not self.filled_at:
            self.filled_at = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['shift__date', 'position__code']


# --- Model 6: ShiftChangeRequest (For trading/dropping shifts) ---

class ShiftChangeRequest(models.Model):
    """
    Handles requests to trade or drop shifts after they've been claimed.
    Requires officer approval.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    REQUEST_TYPES = [
        ('DROP', 'Drop Shift'),
        ('TRADE', 'Trade Shift'),
    ]
    
    shift_slot = models.ForeignKey(ShiftSlot, on_delete=models.CASCADE, related_name='change_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shift_change_requests')
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPES)
    
    # For trade requests
    trade_with = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_trade_requests')
    
    # Approval tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_shift_changes')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Justification
    reason = models.TextField(help_text="Reason for the change request.")
    admin_notes = models.TextField(blank=True, help_text="Notes from the reviewing officer.")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.request_type} request by {self.requested_by.get_full_name()} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
