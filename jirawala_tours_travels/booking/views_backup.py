from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
import traceback
import decimal

from .models import Inquiry, CarType, Car, PopularRoute, BookingStatusHistory
from .serializers import InquirySerializer, BookingCreateSerializer

logger = logging.getLogger(__name__)


# ✅ CUSTOM ADMIN VIEWS
def is_admin_user(user):
    """Check if user is admin (superuser or staff)"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def custom_admin_login(request):
    """Custom admin login view"""
    if request.user.is_authenticated and is_admin_user(request.user):
        return redirect('custom_admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and is_admin_user(user):
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('custom_admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'custom_admin/login.html')


@login_required
@user_passes_test(is_admin_user)
def custom_admin_logout(request):
    """Custom admin logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('custom_admin_login')


@login_required
@user_passes_test(is_admin_user)
def custom_admin_dashboard(request):
    """Custom admin dashboard"""
    # Get statistics
    total_bookings = Inquiry.objects.count()
    pending_bookings = Inquiry.objects.filter(status='pending').count()
    confirmed_bookings = Inquiry.objects.filter(status='confirmed').count()
    completed_bookings = Inquiry.objects.filter(status='completed').count()
    
    # Recent bookings
    recent_bookings = Inquiry.objects.order_by('-created_at')[:10]
    
    # Monthly stats
    current_month = timezone.now().replace(day=1)
    monthly_bookings = Inquiry.objects.filter(created_at__gte=current_month).count()
    
    # Revenue calculation (this month)
    monthly_revenue = sum([float(booking.price) for booking in Inquiry.objects.filter(created_at__gte=current_month)])
    
    context = {
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'completed_bookings': completed_bookings,
        'recent_bookings': recent_bookings,
        'monthly_bookings': monthly_bookings,
        'monthly_revenue': monthly_revenue,
        'user': request.user,
    }
    
    return render(request, 'custom_admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def custom_admin_bookings(request):
    """Custom admin bookings list"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date_filter', '')
    
    # Base queryset
    bookings = Inquiry.objects.all().order_by('-created_at')
    
    # Apply filters
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    if search_query:
        bookings = bookings.filter(
            Q(booking_id__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(origin__icontains=search_query) |
            Q(destination__icontains=search_query)
        )
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            bookings = bookings.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            bookings = bookings.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            bookings = bookings.filter(created_at__date__gte=month_ago)
    
    # Pagination
    paginator = Paginator(bookings, 20)  # Show 20 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'date_filter': date_filter,
        'status_choices': Inquiry.STATUS_CHOICES,
    }
    
    return render(request, 'custom_admin/bookings.html', context)


@login_required
@user_passes_test(is_admin_user)
def custom_admin_booking_detail(request, booking_id):
    """Custom admin booking detail view"""
    booking = get_object_or_404(Inquiry, id=booking_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            old_status = booking.status
            
            if new_status in dict(Inquiry.STATUS_CHOICES):
                booking.status = new_status
                booking.save()
                
                # Create status history
                BookingStatusHistory.objects.create(
                    inquiry=booking,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=request.user.username,
                    notes=f'Status updated by {request.user.username}'
                )
                
                messages.success(request, f'Booking status updated to {booking.get_status_display()}')
                return redirect('custom_admin_booking_detail', booking_id=booking.id)
        
        elif action == 'assign_car':
            car_id = request.POST.get('car_id')
            if car_id:
                car = get_object_or_404(Car, id=car_id)
                booking.assigned_car = car
                booking.save()
                messages.success(request, f'Car {car.name} assigned to booking')
                return redirect('custom_admin_booking_detail', booking_id=booking.id)
        
        elif action == 'add_note':
            note = request.POST.get('admin_notes')
            if note:
                booking.admin_notes = note
                booking.save()
                messages.success(request, 'Admin note added successfully')
                return redirect('custom_admin_booking_detail', booking_id=booking.id)
    
    # Get available cars of the same type
    available_cars = Car.objects.filter(
        car_type=booking.car_type,
        is_available=True
    ) if booking.car_type else Car.objects.none()
    
    # Get status history
    status_history = booking.status_history.all().order_by('-changed_at')
    
    context = {
        'booking': booking,
        'available_cars': available_cars,
        'status_history': status_history,
        'status_choices': Inquiry.STATUS_CHOICES,
    }
    
    return render(request, 'custom_admin/booking_detail.html', context)


@login_required
@user_passes_test(is_admin_user)
def custom_admin_cars(request):
    """Custom admin cars management"""
    cars = Car.objects.all().order_by('car_type', 'name')
    car_types = CarType.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_car':
            name = request.POST.get('name')
            registration = request.POST.get('registration_number')
            car_type_id = request.POST.get('car_type')
            driver_name = request.POST.get('driver_name', '')
            driver_contact = request.POST.get('driver_contact', '')
            
            if name and registration and car_type_id:
                car_type = get_object_or_404(CarType, id=car_type_id)
                Car.objects.create(
                    name=name,
                    registration_number=registration,
                    car_type=car_type,
                    driver_name=driver_name,
                    driver_contact=driver_contact
                )
                messages.success(request, f'Car {name} added successfully')
                return redirect('custom_admin_cars')
    
    context = {
        'cars': cars,
        'car_types': car_types,
    }
    
    return render(request, 'custom_admin/cars.html', context)


def safe_decimal_convert(value, default=None):
    """Safely convert a value to decimal, returning default if conversion fails"""
    if value is None or value == '':
        return default
    
    try:
        # Handle string values that might have extra whitespace
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
        
        # Convert to Decimal
        return decimal.Decimal(str(value))
    except (ValueError, TypeError, decimal.InvalidOperation, decimal.ConversionSyntax):
        logger.warning(f"Could not convert '{value}' to decimal, using default: {default}")
        return default


@login_required
@user_passes_test(is_admin_user)
def custom_admin_routes(request):
    """Custom admin popular routes management"""
    routes = []
    
    try:
        # Get all routes and handle any data issues
        all_routes = PopularRoute.objects.all().order_by('origin', 'destination')
        
        for route in all_routes:
            try:
                # Create a safe route object with validated data
                safe_route = {
                    'id': route.id,
                    'origin': route.origin or '',
                    'destination': route.destination or '',
                    'distance_km': safe_decimal_convert(route.distance_km),
                    'rate': safe_decimal_convert(route.rate),
                    'is_active': route.is_active,
                    'created_at': route.created_at,
                }
                
                routes.append(safe_route)
                
            except Exception as route_error:
                logger.error(f"Error processing route {route.id}: {str(route_error)}")
                # Skip this route but continue with others
                continue
            
    except Exception as e:
        logger.error(f"Error loading routes: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error loading routes. Please check the data integrity.')
        routes = []
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_route':
            origin = request.POST.get('origin', '').strip()
            destination = request.POST.get('destination', '').strip()
            rate = request.POST.get('rate', '').strip()
            distance = request.POST.get('distance_km', '').strip()
            
            if origin and destination and rate and distance:
                try:
                    # Validate and convert decimal values using our safe function
                    rate_decimal = safe_decimal_convert(rate)
                    distance_decimal = safe_decimal_convert(distance)
                    
                    if rate_decimal is None or distance_decimal is None:
                        messages.error(request, 'Invalid rate or distance value. Please enter valid numbers.')
                        return redirect('custom_admin_routes')
                    
                    # Check for negative values
                    if rate_decimal <= 0 or distance_decimal <= 0:
                        messages.error(request, 'Rate and distance must be positive numbers.')
                        return redirect('custom_admin_routes')
                    
                    # Create the route
                    new_route = PopularRoute.objects.create(
                        origin=origin,
                        destination=destination,
                        rate=rate_decimal,
                        distance_km=distance_decimal,
                        is_active=True
                    )
                    
                    messages.success(request, f'Route {origin} → {destination} added successfully')
                    logger.info(f"Route created successfully: {new_route.id}")
                    
                except Exception as e:
                    messages.error(request, f'Error adding route: {str(e)}')
                    logger.error(f"Error creating route: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                messages.error(request, 'Please fill in all required fields.')
                
            return redirect('custom_admin_routes')
    
    context = {
        'routes': routes,
    }
    
    return render(request, 'custom_admin/routes.html', context)


# ✅ EXISTING API VIEWS (keeping them as they were)
class InquiryViewSet(viewsets.ModelViewSet):
    queryset = Inquiry.objects.all().order_by('-created_at')
    serializer_class = InquirySerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_serializer_class(self):
        if self.action == 'create_booking':
            return BookingCreateSerializer
        return InquirySerializer
    
    @action(detail=False, methods=['post'], url_path='create-booking')
    def create_booking(self, request):
        """Create booking from frontend form data"""
        try:
            logger.info(f"📥 Received booking data: {request.data}")
            
            # Validate the incoming data
            serializer = BookingCreateSerializer(data=request.data)
            if serializer.is_valid():
                logger.info("✅ Serializer validation passed")
                
                # Try to create the inquiry
                try:
                    inquiry = serializer.save()
                    logger.info(f"✅ Booking created successfully: {inquiry.booking_id}")
                    
                    return Response({
                        'success': True,
                        'message': 'Booking created successfully',
                        'booking_id': inquiry.booking_id,
                        'data': {
                            'id': inquiry.id,
                            'booking_id': inquiry.booking_id,
                            'name': inquiry.name,
                            'email': inquiry.email,
                            'phone': inquiry.number,
                            'pickup_location': inquiry.origin,
                            'dropoff_location': inquiry.destination,
                            'pickup_date': inquiry.datetime.isoformat(),
                            'dropoff_date': inquiry.return_datetime.isoformat() if inquiry.return_datetime else None,
                            'car_type': inquiry.car_type.name if inquiry.car_type else None,
                            'trip_type': inquiry.trip_type,
                            'distance': float(inquiry.distance_km),
                            'total_price': float(inquiry.price),
                            'status': inquiry.status,
                            'created_at': inquiry.created_at.isoformat()
                        }
                    }, status=status.HTTP_201_CREATED)
                    
                except Exception as save_error:
                    logger.error(f"❌ Error saving inquiry: {str(save_error)}")
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    
                    # Check if it's a database error
                    if 'no such table' in str(save_error).lower():
                        return Response({
                            'success': False,
                            'error': 'Database not properly initialized. Please run migrations.',
                            'details': str(save_error)
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    return Response({
                        'success': False,
                        'error': 'Error saving booking to database.',
                        'details': str(save_error)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            else:
                logger.error(f"❌ Validation errors: {serializer.errors}")
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"❌ Unexpected error creating booking: {str(e)}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': 'An unexpected error occurred. Please try again.',
                'details': str(e) if logger.level == logging.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='by-booking-id')
    def get_by_booking_id(self, request):
        """Get booking by booking ID"""
        booking_id = request.query_params.get('booking_id')
        
        if not booking_id:
            return Response({
                'success': False,
                'error': 'booking_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inquiry = Inquiry.objects.get(booking_id=booking_id)
            serializer = self.get_serializer(inquiry)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Inquiry.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Booking not found'
            }, status=status.HTTP_404_NOT_FOUND)


def index(request):
    """Main homepage view"""
    return render(request, "index.html")


def popular_routes(request):
    """Popular routes page view"""
    # You can add context data here if needed
    context = {
        'page_title': 'Popular Routes',
        'page_description': 'Explore our most requested intercity taxi services',
    }
    return render(request, "popular-routes.html", context)


def blogs(request):
    """Blogs page view"""
    # You can add context data here if needed
    context = {
        'page_title': 'Our Blogs',
        'page_description': 'Read our latest travel tips, destination guides, and industry insights',
    }
    return render(request, "blogs.html", context)


# Legacy API endpoint for backward compatibility
@method_decorator(csrf_exempt, name='dispatch')
class BookingAPIView(View):
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            logger.info(f"Legacy API - Received booking data: {data}")
            
            serializer = BookingCreateSerializer(data=data)
            if serializer.is_valid():
                inquiry = serializer.save()
                
                return JsonResponse({
                    'success': True,
                    'booking_id': inquiry.booking_id,
                    'message': 'Booking created successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=400)
                
        except Exception as e:
            logger.error(f"Legacy API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# Route proxy for distance calculation
import requests

@csrf_exempt
def route_proxy(request):
    if request.method == "POST":
        body = request.body
        headers = {
            "Authorization": "your_openrouteservice_api_key_here",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.openrouteservice.org/v2/directions/driving-car",
            data=body,
            headers=headers
        )
        return JsonResponse(response.json(), status=response.status_code)
