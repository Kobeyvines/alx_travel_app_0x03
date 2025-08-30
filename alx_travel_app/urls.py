from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from listings.views import ListingViewSet, BookingViewSet, initiate_payment, verify_payment

router = DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/payments/initiate/', initiate_payment, name='initiate-payment'),
    path('api/payments/verify/<str:tx_ref>/', verify_payment, name='verify-payment'),
]
