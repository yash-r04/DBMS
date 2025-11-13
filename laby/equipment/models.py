from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Staff', 'Staff'),
        ('Viewer', 'Viewer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=15)
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
    datasheet = models.FileField(upload_to='datasheets/', blank=True, null=True)
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class UsageRecord(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='usage_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_records')
    borrowed_on = models.DateField()
    returned_on = models.DateField(null=True, blank=True)
    purpose = models.TextField()
    quantity_used = models.PositiveIntegerField()

class Alert(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # <- Add this

    

class EquipmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # the viewer requesting
    equipment = models.ForeignKey('Equipment', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    purpose = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} requested {self.quantity} {self.equipment.name}"

