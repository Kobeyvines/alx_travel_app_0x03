import json
import uuid
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import viewsets
from .models import Listing, Booking, Payment
from .tasks import send_payment_confirmation_email
from .serializers import ListingSerializer, BookingSerializer

CHAPA_INIT_URL = "https://api.chapa.co/v1/transaction/initialize"
CHAPA_VERIFY_URL = "https://api.chapa.co/v1/transaction/verify/{tx_ref}"


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

def _auth_headers():
    return {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        "Content-Type": "application/json",
    }

@csrf_exempt
def initiate_payment(request):
    """
    POST JSON: { "booking_id": 123 }
    Creates Payment(Pending), calls Chapa initialize, saves checkout_url, returns it.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        body = json.loads(request.body.decode("utf-8"))
        booking_id = body["booking_id"]
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    booking = get_object_or_404(Booking, id=booking_id)

    # Use booking total/price; adjust field name as needed
    amount = getattr(booking, "total_price", None) or getattr(booking, "price", None)
    if amount is None:
        return HttpResponseBadRequest("Booking has no amount field")

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

    payload = {
        "amount": str(amount),
        "currency": payment.currency,
        # Supply user/customer details if you have them on the booking
        "email": getattr(getattr(booking, "user", None), "email", "customer@example.com"),
        "first_name": getattr(getattr(booking, "user", None), "first_name", "Guest"),
        "last_name": getattr(getattr(booking, "user", None), "last_name", "User"),
        "tx_ref": payment.tx_ref,
        # Chapa will redirect and/or call these
        "return_url": settings.CHAPA_RETURN_URL,
        "callback_url": settings.CHAPA_CALLBACK_URL,
        "customization": {
            "title": "ALX Travel Booking",
            "description": f"Booking #{booking.id}",
        },
    }

    resp = requests.post(CHAPA_INIT_URL, headers=_auth_headers(), json=payload, timeout=30)
    data = resp.json()

    # Expected: data["data"]["checkout_url"]; see docs. :contentReference[oaicite:1]{index=1}
    if resp.status_code == 200 and data.get("status") == "success":
        checkout_url = data["data"]["checkout_url"]
        payment.checkout_url = checkout_url
        payment.save(update_fields=["checkout_url", "updated_at"])
        return JsonResponse({"status": "ok", "tx_ref": payment.tx_ref, "checkout_url": checkout_url})

    # Failure path
    payment.status = Payment.STATUS_FAILED
    payment.save(update_fields=["status", "updated_at"])
    return JsonResponse({"status": "error", "detail": data}, status=400)

@csrf_exempt
def verify_payment(request, tx_ref: str):
    """
    GET /api/payments/verify/<tx_ref>/
    Calls Chapa verify endpoint and updates Payment.status accordingly.
    """
    payment = get_object_or_404(Payment, tx_ref=tx_ref)

    url = CHAPA_VERIFY_URL.format(tx_ref=tx_ref)
    resp = requests.get(url, headers=_auth_headers(), timeout=30)
    data = resp.json()

    # Expected verify endpoint: GET with Bearer, status in response. :contentReference[oaicite:2]{index=2}
    if resp.status_code == 200 and data.get("status") == "success":
        # Chapa often returns fields like data.status, data.reference, data.tx_ref
        d = data.get("data", {})
        chapa_status = d.get("status", "").lower()
        payment.chapa_ref = d.get("reference") or d.get("ref_id", "") or payment.chapa_ref

        if chapa_status == "success":
            payment.status = Payment.STATUS_COMPLETED
        elif chapa_status in {"failed", "cancelled"}:
            payment.status = Payment.STATUS_FAILED
        else:
            payment.status = Payment.STATUS_PENDING
            
        if payment.status == Payment.STATUS_COMPLETED:
            user_email = getattr(getattr(payment.booking, "user", None), "email", None)
            if user_email:
                send_payment_confirmation_email.delay(user_email, payment.booking.id, str(payment.amount))


        payment.save(update_fields=["status", "chapa_ref", "updated_at"])
        return JsonResponse({"status": "ok", "payment_status": payment.status, "data": d})

    return JsonResponse({"status": "error", "detail": data}, status=400)

@csrf_exempt
def chapa_callback(request):
    """
    Chapa calls this after payment (your callback_url).
    Per docs, you'll get tx_ref + status; always verify server-side. :contentReference[oaicite:3]{index=3}
    """
    if request.method not in ("GET", "POST"):
        return HttpResponseBadRequest("Unsupported method")

    try:
        if request.method == "POST" and request.body:
            payload = json.loads(request.body.decode("utf-8"))
        else:
            # some integrations send query params
            payload = {k: v for k, v in request.GET.items()}
    except Exception:
        payload = {}

    tx_ref = payload.get("tx_ref") or payload.get("trx_ref")  # docs show trx_ref in examples
    if not tx_ref:
        return HttpResponseBadRequest("Missing tx_ref")

    # delegate to our verify flow
    url = reverse("payments-verify", kwargs={"tx_ref": tx_ref})
    return JsonResponse({"message": "received", "verify": url})
