from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_payment_confirmation_email(email, booking_id, amount):
    send_mail(
        subject="Booking payment confirmed",
        message=f"Your booking #{booking_id} has been paid. Amount: {amount}",
        from_email="noreply@example.com",
        recipient_list=[email],
        fail_silently=True,
    )
