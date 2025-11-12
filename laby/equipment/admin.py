from django.contrib import admin
from .models import User, Supplier, Equipment, UsageRecord, Alert

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_no', 'city')

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'condition', 'location', 'added_on')
    search_fields = ('name', 'category')

@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'borrowed_on', 'returned_on', 'quantity_used')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'type', 'created_at')
