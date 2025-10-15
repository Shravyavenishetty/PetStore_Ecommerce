from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Booking)
def send_status_change_email(sender, instance, created, **kwargs):
    if not created:
        subject = f"Booking status updated to {instance.get_status_display()}"
        message = f"Hello {instance.user.first_name},\n\nYour booking for {instance.service.title} on {instance.booking_date} at {instance.booking_time} is now '{instance.get_status_display()}'.\n\nThank you."
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email or instance.user.email])
