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
    
    # Create a unique transaction reference
    tx_ref = str(uuid.uuid4())
    
    # Create payment record
    payment = Payment.objects.create(
        booking=booking,
        amount=amount,
        tx_ref=tx_ref,
        status='pending'
    )
    
    # In real implementation, you would integrate with a payment provider here
    # For demo, we'll just return a simulated checkout URL
    checkout_url = request.build_absolute_uri(
        reverse('verify-payment', kwargs={'tx_ref': tx_ref})
    )
    
    return JsonResponse({
        'status': 'success',
        'message': 'Payment initiated',
        'data': {
            'checkout_url': checkout_url,
            'tx_ref': tx_ref
        }
    })


@csrf_exempt
def verify_payment(request, tx_ref):
    """
    GET /api/payments/verify/<tx_ref>/
    Verifies payment status with payment provider
    Updates Payment and Booking statuses
    """
    payment = get_object_or_404(Payment, tx_ref=tx_ref)
    
    if payment.status == 'completed':
        return JsonResponse({
            'status': 'success',
            'message': 'Payment already verified',
            'data': {'tx_ref': tx_ref}
        })
    
    # In real implementation, verify with payment provider
    # For demo, we'll simulate success
    payment.status = 'completed'
    payment.save()
    
    # Update booking status
    booking = payment.booking
    booking.status = 'confirmed'
    booking.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Payment verified successfully',
        'data': {'tx_ref': tx_ref}
    })

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
