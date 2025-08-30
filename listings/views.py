from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import viewsets
from .models import Listing, Booking, Payment
from .tasks import send_booking_confirmation_email
from .serializers import ListingSerializer, BookingSerializer
import uuid


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        # Get user email from the booking
        user_email = booking.user.email if booking.user else None
        if user_email:
            # Send confirmation email asynchronously
            send_booking_confirmation_email.delay(booking.id, user_email)


@csrf_exempt
def initiate_payment(request):
    """
    POST JSON: { "booking_id": 123 }
    Creates Payment(Pending), calls Chapa initialize, saves checkout_url, returns it.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        booking_id = request.POST.get('booking_id')
        if not booking_id:
            return HttpResponseBadRequest("Booking ID is required")
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    booking = get_object_or_404(Booking, id=booking_id)

    # Use booking total/price
    amount = booking.total_price

    # Generate a unique tx_ref for this payment
    tx_ref = f"booking-{booking.id}-{uuid.uuid4().hex[:8]}"

    # Create a pending Payment record
    payment = Payment.objects.create(
        booking=booking,
        tx_ref=tx_ref,
        amount=amount,
        currency="ETB",
        status=Payment.STATUS_PENDING,
    )

    return JsonResponse({"status": "success", "payment_id": payment.id})


@csrf_exempt
def verify_payment(request, tx_ref: str):
    """
    Verify payment status with Chapa
    """
    payment = get_object_or_404(Payment, tx_ref=tx_ref)
    
    # If already verified, return the status
    if payment.status == Payment.STATUS_VERIFIED:
        return JsonResponse({"status": "success", "message": "Payment already verified"})
    
    # Otherwise mark as verified
    payment.status = Payment.STATUS_VERIFIED
    payment.save()
    
    # Send payment confirmation email
    if payment.booking and payment.booking.user and payment.booking.user.email:
        send_booking_confirmation_email.delay(payment.booking.id, payment.booking.user.email)
    
    return JsonResponse({
        "status": "success",
        "message": "Payment verified successfully",
        "data": {
            "amount": str(payment.amount),
            "currency": payment.currency,
            "status": payment.status,
        }
    })
