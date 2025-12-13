from django.db import models
from django.contrib.auth.models import User

# --- Choices for Asset Status ---
ASSET_STATUS_CHOICES = [
    ('SERVICE', 'In Service'),
    ('OUT', 'Out of Service (Repair/Maint)'),
    ('RETIRED', 'Retired/Disposed'),
]

# --- Model 1: Category (for Assets) ---

class Category(models.Model):
    """
    Used to group assets (e.g., 'SCBA Equipment', 'Vehicles', 'Office Supplies').
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']


# --- Model 2: Asset ---

class Asset(models.Model):
    """
    Represents a single, trackable piece of equipment or property.
    """
    # Core Identification
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    asset_tag = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Department's internal asset ID.")
    
    # Location and Status
    location = models.CharField(max_length=100, help_text="Where the asset is physically located (e.g., Engine 1, Station 2 storage).")
    status = models.CharField(max_length=10, choices=ASSET_STATUS_CHOICES, default='SERVICE')
    
    # Financial/Acquisition Info
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Maintenance/Compliance Info
    last_inspection_date = models.DateField(null=True, blank=True)
    next_inspection_date = models.DateField(null=True, blank=True)
    
    # Metadata
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.asset_tag or self.serial_number})"

    class Meta:
        ordering = ['category__name', 'asset_tag']


# --- Model 3: MaintenanceLog ---

class MaintenanceLog(models.Model):
    """
    Logs every time an asset is serviced, repaired, or inspected.
    """
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_logs')
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    date_of_service = models.DateField()
    description = models.TextField(help_text="Details of the work performed, repair, or inspection findings.")
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Optional field to update the asset's next inspection date
    new_next_inspection_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Service on {self.asset.asset_tag} on {self.date_of_service}"

    class Meta:
        ordering = ['-date_of_service']


# --- Model 4: SupplyRequest ---

class SupplyRequest(models.Model):
    """
    Represents a request from a member for supplies (non-asset items).
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('ORDERED', 'Ordered'),
        ('FULFILLED', 'Fulfilled'),
        ('REJECTED', 'Rejected'),
    ]
    
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supply_requests')
    request_date = models.DateTimeField(auto_now_add=True)
    
    item_description = models.CharField(max_length=255, help_text="Name and detailed description of the item needed.")
    quantity = models.IntegerField(default=1)
    justification = models.TextField()
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    # Quartermaster fields
    quartermaster_notes = models.TextField(blank=True)
    date_processed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request by {self.requested_by.username} for {self.item_description} ({self.status})"

    class Meta:
        ordering = ['status', '-request_date']
