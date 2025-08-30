from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_booking_confirmation_email(booking_id, user_email):
    """
    Send a confirmation email to the user when a booking is created
    """
    subject = 'Booking Confirmation'
    message = f'Thank you for your booking (ID: {booking_id})! Your reservation has been confirmed.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )

    return f'Confirmation email sent for booking {booking_id}'
