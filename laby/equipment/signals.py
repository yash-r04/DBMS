from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UsageRecord, Alert, Equipment

@receiver(post_save, sender=UsageRecord)
def handle_damage_and_alert(sender, instance, created, **kwargs):

    # Create alert only when damage is reported
    if instance.is_damaged and instance.damage_report:
        Alert.objects.get_or_create(
            equipment=instance.equipment,
            message=f"Damage reported: {instance.damage_report[:100]}...",
            defaults={"is_active": True}
        )

    # Auto-deduct inventory if damaged AND not already processed
    if instance.is_damaged and not instance.damage_processed:

        equipment = instance.equipment
        quantity_to_deduct = instance.quantity_used

        if equipment.quantity >= quantity_to_deduct:
            equipment.quantity -= quantity_to_deduct
        else:
            equipment.quantity = 0  # Prevent negative inventory

        equipment.save()

        # Mark as processed so deduction doesn't repeat
        instance.damage_processed = True
        instance.save(update_fields=["damage_processed"])
