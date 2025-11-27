from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Staff', 'Staff'),
        ('Viewer', 'Viewer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=15)
    equipments_available = models.CharField(max_length=50, default="N/A")
    email = models.EmailField()
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class Equipment(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    quantity = models.IntegerField()
    location = models.CharField(max_length=100)
    condition = models.CharField(max_length=50, default='Good')
    added_on = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True, help_text="Short description or usage of the equipment")
    datasheet = models.URLField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class UsageRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity_used = models.PositiveIntegerField(default=1)
    borrowed_on = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    returned_on = models.DateField(null=True, blank=True)

    is_damaged = models.BooleanField(default=False)
    damage_report = models.TextField(blank=True, null=True)

    approved_by = models.ForeignKey(User, related_name="approved_records",
                                    on_delete=models.SET_NULL, null=True, blank=True)
    collected_by = models.ForeignKey(User, related_name="collected_records",
                                     on_delete=models.SET_NULL, null=True, blank=True)

    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    damage_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.equipment.name}"



class Alert(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    

class EquipmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    equipment = models.ForeignKey('Equipment', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    purpose = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} requested {self.quantity} {self.equipment.name}"

