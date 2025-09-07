from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Listing, Booking, Payment, Review
from .tasks import send_booking_confirmation_email
from .serializers import (
    ListingSerializer, BookingSerializer, PaymentSerializer,
    ReviewSerializer
)
import uuid


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a specific listing"""
        listing = self.get_object()
        reviews = Review.objects.filter(listing=listing)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        booking = serializer.save(user=self.request.user)
        if booking.user.email:
            send_booking_confirmation_email.delay(booking.id, booking.user.email)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.select_related('user', 'listing').all()

    def list(self, request, *args, **kwargs):
        # Filter reviews by listing_id if provided
        listing_id = request.query_params.get('listing_id')
        queryset = self.get_queryset()
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@csrf_exempt
def initiate_payment(request):
    """Initiate a new payment for a booking"""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        booking_id = request.POST.get('booking_id')
        if not booking_id:
            return HttpResponseBadRequest("Booking ID is required")
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    booking = get_object_or_404(Booking, id=booking_id)
    amount = booking.total_price
    tx_ref = f"booking-{booking.id}-{uuid.uuid4().hex[:8]}"

    payment = Payment.objects.create(
        booking=booking,
        amount=amount,
        tx_ref=tx_ref,
        status=Payment.STATUS_PENDING
    )

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
    """Verify payment status and update booking"""
    payment = get_object_or_404(Payment, tx_ref=tx_ref)
    
    if payment.status == Payment.STATUS_VERIFIED:
        return JsonResponse({
            'status': 'success',
            'message': 'Payment already verified'
        })
    
    payment.status = Payment.STATUS_VERIFIED
    payment.save()

    if payment.booking:
        payment.booking.status = Booking.STATUS_CONFIRMED
        payment.booking.save()
        
        if payment.booking.user and payment.booking.user.email:
            send_booking_confirmation_email.delay(payment.booking.id, payment.booking.user.email)
    
    return JsonResponse({
        'status': 'success',
        'message': 'Payment verified successfully',
        'data': {
            'amount': str(payment.amount),
            'currency': payment.currency,
            'status': payment.status
        }
    })
