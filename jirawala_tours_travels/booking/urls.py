from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InquiryViewSet, index, BookingAPIView, popular_routes, gallery,
    # Custom Admin Views
    custom_admin_login, custom_admin_logout, custom_admin_dashboard,
    custom_admin_bookings, custom_admin_booking_detail, custom_admin_cars,
    custom_admin_routes, custom_admin_car_edit, get_car_types_api, custom_admin_gallery,
    # Car Integration Views
    our_cars, car_availability_check, car_specific_booking, custom_admin_car_types,
    # Image serving views
    serve_car_image, serve_route_image, get_car_image_info, get_route_image_info,
    # Gallery views
    serve_gallery_image, get_gallery_image_info, get_gallery_data_api,
    # Tooltip
    get_available_cars_by_type,
)

router = DefaultRouter()
router.register(r'inquiry', InquiryViewSet, basename='inquiry')

urlpatterns = [
    # ✅ MAIN WEBSITE URLS
    path('', index, name='home'),
    path('popular-routes/', popular_routes, name='popular_routes'),
    path('our-cars/', our_cars, name='our_cars'),
    path('gallery/', gallery, name='gallery'),

    
    # ✅ API ENDPOINTS
    path('api/', include(router.urls)),
    path('api/bookings/', BookingAPIView.as_view(), name='booking_api'),
    path('api/car-types/', get_car_types_api, name='get_car_types_api'),
    path('api/gallery/', get_gallery_data_api, name='get_gallery_data_api'),
    path('api/gallery-data/', get_gallery_data_api, name='get_gallery_image_info'),
    path('api/available-cars-by-type/', get_available_cars_by_type, name='available_cars_by_type'),

    # Car-specific API endpoints
    path('api/car-availability/', car_availability_check, name='car_availability_check'),
    path('api/car-booking/', car_specific_booking, name='car_specific_booking'),
    
    # IMAGE SERVING ENDPOINTS
    path('api/images/car/<int:car_id>/', serve_car_image, name='serve_car_image'),
    path('api/images/route/<int:route_id>/', serve_route_image, name='serve_route_image'),
    path('api/images/car/<int:car_id>/info/', get_car_image_info, name='car_image_info'),
    path('api/images/route/<int:route_id>/info/', get_route_image_info, name='route_image_info'),
    path('api/images/gallery/<int:gallery_id>/', serve_gallery_image, name='serve_gallery_image'),
    path('api/images/gallery/<int:gallery_id>/info/', get_gallery_image_info, name='gallery_image_info'),
    path('serve_gallery_image/<int:gallery_id>/', serve_gallery_image, name='serve_gallery_image_legacy'),
    
    # CUSTOM ADMIN URLS
    path('admin-panel/', custom_admin_login, name='custom_admin_login'),
    path('admin-panel/logout/', custom_admin_logout, name='custom_admin_logout'),
    path('admin-panel/dashboard/', custom_admin_dashboard, name='custom_admin_dashboard'),
    path('admin-panel/bookings/', custom_admin_bookings, name='custom_admin_bookings'),
    path('admin-panel/bookings/<int:booking_id>/', custom_admin_booking_detail, name='custom_admin_booking_detail'),
    path('admin-panel/cars/', custom_admin_cars, name='custom_admin_cars'),
    path('admin-panel/car-types/', custom_admin_car_types, name='custom_admin_car_types'),
    path('admin-panel/routes/', custom_admin_routes, name='custom_admin_routes'),
    path('admin-panel/cars/edit/<int:car_id>/', custom_admin_car_edit, name='custom_admin_car_edit'),
    path('admin-panel/gallery/', custom_admin_gallery, name='custom_admin_gallery'),
]
