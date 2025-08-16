from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet
from listings.views import initiate_payment, verify_payment, chapa_callback

router = DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/payments/initiate/', initiate_payment, name='payments-initiate'),
    path('api/payments/verify/<str:tx_ref>/', verify_payment, name='payments-verify'),
    path('api/payments/callback/', chapa_callback, name='payments-callback'),
    path('payments/return/', lambda r: HttpResponse("Payment return page OK")),  # simple placeholder
]
