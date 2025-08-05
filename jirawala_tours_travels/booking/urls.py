from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InquiryViewSet, index, BookingAPIView, popular_routes, blogs,
    # Custom Admin Views
    custom_admin_login, custom_admin_logout, custom_admin_dashboard,
    custom_admin_bookings, custom_admin_booking_detail, custom_admin_cars,
    custom_admin_routes, custom_admin_car_edit,  # NEW: Car edit functionality
    # Car Integration Views
    our_cars, car_availability_check, car_specific_booking
)

router = DefaultRouter()
router.register(r'inquiry', InquiryViewSet, basename='inquiry')

urlpatterns = [
    # ✅ MAIN WEBSITE URLS
    path('', index, name='home'),                    # Main page
    path('popular-routes/', popular_routes, name='popular_routes'),  # Popular routes page
    path('blogs/', blogs, name='blogs'),             # Blogs page
    path('our-cars/', our_cars, name='our_cars'),    # Our Cars page
    
    # ✅ API ENDPOINTS
    path('api/', include(router.urls)),              # API endpoints
    path('api/bookings/', BookingAPIView.as_view(), name='booking_api'),  # Legacy API

    # Car-specific API endpoints
    path('api/car-availability/', car_availability_check, name='car_availability_check'),
    path('api/car-booking/', car_specific_booking, name='car_specific_booking'),
    
    # ✅ CUSTOM ADMIN URLS
    path('admin-panel/', custom_admin_login, name='custom_admin_login'),
    path('admin-panel/logout/', custom_admin_logout, name='custom_admin_logout'),
    path('admin-panel/dashboard/', custom_admin_dashboard, name='custom_admin_dashboard'),
    path('admin-panel/bookings/', custom_admin_bookings, name='custom_admin_bookings'),
    path('admin-panel/bookings/<int:booking_id>/', custom_admin_booking_detail, name='custom_admin_booking_detail'),
    path('admin-panel/cars/', custom_admin_cars, name='custom_admin_cars'),
    path('admin-panel/routes/', custom_admin_routes, name='custom_admin_routes'),
    path('admin-panel/cars/edit/<int:car_id>/', custom_admin_car_edit, name='custom_admin_car_edit'),  # Keep car edit URL
]
