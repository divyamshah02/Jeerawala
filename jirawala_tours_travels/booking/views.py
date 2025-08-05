from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import connection
import json
import logging
import traceback
import decimal

from .models import Inquiry, CarType, Car, PopularRoute, BookingStatusHistory
from .serializers import InquirySerializer, BookingCreateSerializer, CarSerializer

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

logger = logging.getLogger(__name__)

# ✅ HELPER FUNCTION - SINGLE SOURCE OF TRUTH FOR ROUTES DATA
def get_routes_data():
    """Get routes data consistently for all views"""
    routes = []
    
    try:
        # Use raw SQL to avoid decimal issues
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, origin, destination, distance_km, rate, image
                FROM booking_popularroute 
                WHERE is_active = 1
                ORDER BY origin, destination
            """)
            
            raw_routes = cursor.fetchall()
            
            for row in raw_routes:
                try:
                    route_data = {
                        'id': row[0],
                        'origin': str(row[1]) if row[1] else '',
                        'destination': str(row[2]) if row[2] else '',
                        'distance_km': float(row[3]) if row[3] is not None else 0,
                        'rate': float(row[4]) if row[4] is not None else 0,
                        'image': str(row[-1])
                    }
                    print(route_data)
                    routes.append(route_data)
                except Exception as route_error:
                    logger.error("Error processing route {}: {}".format(row[0], str(route_error)))
                    continue
                    
    except Exception as e:
        logger.error("Error loading routes: {}".format(str(e)))
        routes = []
    
    return routes


# ✅ MAIN VIEWS - FIXED TO USE SAME DATA SOURCE
def index(request):
    """Main homepage view - FIXED"""
    routes = get_routes_data()[:8]  # Limit to 8 for homepage
    
    context = {
        'routes': routes,
    }
    
    return render(request, "index.html", context)


def popular_routes(request):
    """Popular routes page view - FIXED"""
    routes = get_routes_data()  # All routes for this page
    
    context = {
        'page_title': 'Popular Routes',
        'page_description': 'Explore our most requested intercity taxi services',
        'routes': routes,
    }
    
    return render(request, "popular-routes.html", context)


def blogs(request):
    """Blogs page view"""
    context = {
        'page_title': 'Our Blogs',
        'page_description': 'Read our latest travel tips, destination guides, and industry insights',
    }
    return render(request, "blogs.html", context)


# ✅ ADMIN VIEWS (keeping all your existing admin functions)
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
            messages.success(request, 'Welcome back, {}!'.format(user.first_name or user.username))
            return redirect('custom_admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'custom_admin/login.html')


@login_required
def custom_admin_logout(request):
    """Custom admin logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('custom_admin_login')


@login_required
@user_passes_test(is_admin_user)
def custom_admin_dashboard(request):
    """Custom admin dashboard - FIXED DECIMAL HANDLING"""
    try:
        # Get statistics using safe decimal handling
        total_bookings = Inquiry.objects.count()
        pending_bookings = Inquiry.objects.filter(status='pending').count()
        confirmed_bookings = Inquiry.objects.filter(status='confirmed').count()
        completed_bookings = Inquiry.objects.filter(status='completed').count()
        
        # Recent bookings - Use raw SQL to avoid decimal issues
        recent_bookings = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id, booking_id, name, email, origin, destination, 
                        datetime, status, CAST(price AS DECIMAL(10,2)) as safe_price,
                        created_at
                    FROM booking_inquiry 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                
                raw_bookings = cursor.fetchall()
                
                for row in raw_bookings:
                    try:
                        booking_data = {
                            'id': row[0],
                            'booking_id': str(row[1]) if row[1] else '',
                            'name': str(row[2]) if row[2] else '',
                            'email': str(row[3]) if row[3] else '',
                            'origin': str(row[4]) if row[4] else '',
                            'destination': str(row[5]) if row[5] else '',
                            'datetime': row[6],
                            'status': str(row[7]) if row[7] else 'pending',
                            'price': float(row[8]) if row[8] is not None else 0,
                            'created_at': row[9],
                        }
                        
                        # Add status display method
                        status_choices = dict(Inquiry.STATUS_CHOICES)
                        booking_data['get_status_display'] = status_choices.get(booking_data['status'], booking_data['status'].title())

                        # Add URL for booking detail page
                        booking_data['detail_url'] = '/custom-admin/bookings/{}/'.format(booking_data['id'])

                        recent_bookings.append(booking_data)
                    except Exception as booking_error:
                        logger.error("Error processing booking {}: {}".format(row[0], str(booking_error)))
                        continue
                        
        except Exception as bookings_error:
            logger.error("Error loading recent bookings: {}".format(str(bookings_error)))
            recent_bookings = []
        
        # ✅ FIXED: Monthly stats - Set to beginning of month (00:00:00)
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_bookings = Inquiry.objects.filter(created_at__gte=current_month).count()
        
        # ✅ FIXED: Safe revenue calculation - only count confirmed/completed bookings from beginning of month
        monthly_revenue = 0
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COALESCE(SUM(CAST(price AS DECIMAL(10,2))), 0) as total_revenue
                    FROM booking_inquiry 
                    WHERE created_at >= %s 
                    AND price IS NOT NULL 
                    AND price != ''
                    AND status IN ('confirmed', 'completed')
                """, [current_month])
                
                result = cursor.fetchone()
                if result and result[0] is not None:
                    monthly_revenue = float(result[0])
                else:
                    monthly_revenue = 0
                    
        except Exception as revenue_error:
            logger.error("Error calculating monthly revenue: {}".format(str(revenue_error)))
            monthly_revenue = 0
        
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
        
    except Exception as e:
        logger.error("Error in admin dashboard: {}".format(str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        
        # Fallback context with safe defaults
        context = {
            'total_bookings': 0,
            'pending_bookings': 0,
            'confirmed_bookings': 0,
            'completed_bookings': 0,
            'recent_bookings': [],
            'monthly_bookings': 0,
            'monthly_revenue': 0,
            'user': request.user,
        }
        
        messages.error(request, 'Error loading dashboard data. Please check the server logs.')
        return render(request, 'custom_admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def custom_admin_bookings(request):
    """Custom admin bookings list - FIXED DECIMAL HANDLING"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        date_filter = request.GET.get('date_filter', '')
        
        # Build WHERE clause for filters
        where_conditions = []
        params = []
        
        if status_filter:
            where_conditions.append("status = %s")
            params.append(status_filter)
        
        if search_query:
            where_conditions.append("""
                (booking_id LIKE %s OR name LIKE %s OR email LIKE %s OR 
                 origin LIKE %s OR destination LIKE %s)
            """)
            search_param = '%{}%'.format(search_query)
            params.extend([search_param, search_param, search_param, search_param, search_param])
        
        if date_filter:
            today = timezone.now().date()
            if date_filter == 'today':
                where_conditions.append("DATE(created_at) = %s")
                params.append(today)
            elif date_filter == 'week':
                week_ago = today - timedelta(days=7)
                where_conditions.append("DATE(created_at) >= %s")
                params.append(week_ago)
            elif date_filter == 'month':
                month_ago = today - timedelta(days=30)
                where_conditions.append("DATE(created_at) >= %s")
                params.append(month_ago)
        
        # Build final WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM booking_inquiry {}".format(where_clause)
        
        with connection.cursor() as cursor:
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
        
        # Pagination setup
        page_number = int(request.GET.get('page', 1))
        per_page = 20
        offset = (page_number - 1) * per_page
        
        # Get bookings with safe decimal handling
        bookings_query = """
            SELECT 
                id, booking_id, name, email, number, origin, destination, 
                datetime, return_datetime, status, 
                CAST(price AS DECIMAL(10,2)) as safe_price,
                CAST(distance_km AS DECIMAL(8,2)) as safe_distance,
                trip_type, created_at, updated_at
            FROM booking_inquiry 
            {} 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """.format(where_clause)
        
        params.extend([per_page, offset])
        
        bookings = []
        with connection.cursor() as cursor:
            cursor.execute(bookings_query, params)
            raw_bookings = cursor.fetchall()
            
            for row in raw_bookings:
                try:
                    booking_data = {
                        'id': row[0],
                        'booking_id': str(row[1]) if row[1] else '',
                        'name': str(row[2]) if row[2] else '',
                        'email': str(row[3]) if row[3] else '',
                        'number': str(row[4]) if row[4] else '',
                        'origin': str(row[5]) if row[5] else '',
                        'destination': str(row[6]) if row[6] else '',
                        'datetime': row[7],
                        'return_datetime': row[8],
                        'status': str(row[9]) if row[9] else 'pending',
                        'price': float(row[10]) if row[10] is not None else 0,
                        'distance_km': float(row[11]) if row[11] is not None else 0,
                        'trip_type': str(row[12]) if row[12] else 'one-way',
                        'created_at': row[13],
                        'updated_at': row[14],
                    }
                    
                    # Add display methods
                    status_choices = dict(Inquiry.STATUS_CHOICES)
                    trip_choices = dict(Inquiry.TRIP_CHOICES)
                    
                    booking_data['get_status_display'] = status_choices.get(booking_data['status'], booking_data['status'].title())
                    booking_data['get_trip_type_display'] = trip_choices.get(booking_data['trip_type'], booking_data['trip_type'].title())
                    
                    bookings.append(booking_data)
                    
                except Exception as booking_error:
                    logger.error("Error processing booking {}: {}".format(row[0], str(booking_error)))
                    continue
        
        # Create pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_previous = page_number > 1
        has_next = page_number < total_pages
        
        # Create page_obj-like structure for template compatibility
        class PageObj:
            def __init__(self, bookings, page_number, total_pages, has_previous, has_next, total_count):
                self.object_list = bookings
                self.number = page_number
                self.has_previous = has_previous
                self.has_next = has_next
                self.previous_page_number = page_number - 1 if has_previous else None
                self.next_page_number = page_number + 1 if has_next else None
                
                # Create paginator-like object
                class PaginatorLike:
                    def __init__(self, num_pages, count):
                        self.num_pages = num_pages
                        self.count = count
                
                self.paginator = PaginatorLike(total_pages, total_count)
            
            def __iter__(self):
                """Make the PageObj itself iterable for templates"""
                return iter(self.object_list)
        
        page_obj = PageObj(bookings, page_number, total_pages, has_previous, has_next, total_count)
        
        context = {
            'page_obj': page_obj,
            'status_filter': status_filter,
            'search_query': search_query,
            'date_filter': date_filter,
            'status_choices': Inquiry.STATUS_CHOICES,
        }
        
        return render(request, 'custom_admin/bookings.html', context)
        
    except Exception as e:
        logger.error("Error in admin bookings view: {}".format(str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        
        # Fallback with empty data
        class EmptyPageObj:
            def __init__(self):
                self.object_list = []
                self.number = 1
                self.has_previous = False
                self.has_next = False
                self.previous_page_number = None
                self.next_page_number = None
                
                # Create paginator-like object
                class PaginatorLike:
                    def __init__(self):
                        self.num_pages = 1
                        self.count = 0
                
                self.paginator = PaginatorLike()
            
            def __iter__(self):
                """Make the EmptyPageObj itself iterable for templates"""
                return iter(self.object_list)
        
        context = {
            'page_obj': EmptyPageObj(),
            'status_filter': '',
            'search_query': '',
            'date_filter': '',
            'status_choices': Inquiry.STATUS_CHOICES,
        }
        
        messages.error(request, 'Error loading bookings data. Please check the server logs.')
        return render(request, 'custom_admin/bookings.html', context)


@login_required
@user_passes_test(is_admin_user)
def custom_admin_booking_detail(request, booking_id):
    """Custom admin booking detail view - FIXED DECIMAL HANDLING"""
    try:
        # Get booking using raw SQL to avoid decimal issues
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, booking_id, name, email, number, origin, destination, 
                    datetime, return_datetime, status, 
                    CAST(price AS DECIMAL(10,2)) as safe_price,
                    CAST(distance_km AS DECIMAL(8,2)) as safe_distance,
                    trip_type, created_at, updated_at, special_requests, admin_notes,
                    car_type_id, assigned_car_id
                FROM booking_inquiry 
                WHERE id = %s
            """, [booking_id])
            
            booking_data = cursor.fetchone()
            
            if not booking_data:
                messages.error(request, 'Booking not found')
                return redirect('custom_admin_bookings')
            
            # Create booking object-like structure for template compatibility
            class BookingObj:
                def __init__(self, data):
                    self.id = data[0]
                    self.booking_id = str(data[1]) if data[1] else ''
                    self.name = str(data[2]) if data[2] else ''
                    self.email = str(data[3]) if data[3] else ''
                    self.number = str(data[4]) if data[4] else ''
                    self.origin = str(data[5]) if data[5] else ''
                    self.destination = str(data[6]) if data[6] else ''
                    self.datetime = data[7]
                    self.return_datetime = data[8]
                    self.status = str(data[9]) if data[9] else 'pending'
                    self.price = float(data[10]) if data[10] is not None else 0
                    self.distance_km = float(data[11]) if data[11] is not None else 0
                    self.trip_type = str(data[12]) if data[12] else 'one-way'
                    self.created_at = data[13]
                    self.updated_at = data[14]
                    self.special_requests = str(data[15]) if data[15] else ''
                    self.admin_notes = str(data[16]) if data[16] else ''
                    self.car_type_id = data[17]
                    self.assigned_car_id = data[18]
                    
                    # Add display methods
                    status_choices = dict(Inquiry.STATUS_CHOICES)
                    trip_choices = dict(Inquiry.TRIP_CHOICES)
                    
                    self.get_status_display = lambda: status_choices.get(self.status, self.status.title())
                    self.get_trip_type_display = lambda: trip_choices.get(self.trip_type, self.trip_type.title())
                
                # Add car_type property
                @property
                def car_type(self):
                    if self.car_type_id:
                        try:
                            return CarType.objects.get(id=self.car_type_id)
                        except CarType.DoesNotExist:
                            return None
                    return None
                
                # Add assigned_car property
                @property
                def assigned_car(self):
                    if self.assigned_car_id:
                        try:
                            return Car.objects.get(id=self.assigned_car_id)
                        except Car.DoesNotExist:
                            return None
                    return None
                
                # Add save method for form processing
                def save(self):
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                UPDATE booking_inquiry 
                                SET status = %s, assigned_car_id = %s, admin_notes = %s, updated_at = NOW()
                                WHERE id = %s
                            """, [self.status, self.assigned_car_id, self.admin_notes, self.id])
                        return True
                    except Exception as e:
                        logger.error("Error saving booking {}: {}".format(self.id, str(e)))
                        return False
            
            booking = BookingObj(booking_data)
            
    except Exception as e:
        logger.error("Error loading booking detail {}: {}".format(booking_id, str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        messages.error(request, 'Error loading booking details. Please check the server logs.')
        return redirect('custom_admin_bookings')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            old_status = booking.status
            
            if new_status in dict(Inquiry.STATUS_CHOICES):
                try:
                    # Update status using raw SQL
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE booking_inquiry 
                            SET status = %s, updated_at = NOW()
                            WHERE id = %s
                        """, [new_status, booking.id])
                    
                    # Create status history
                    BookingStatusHistory.objects.create(
                        inquiry_id=booking.id,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=request.user.username,
                        notes='Status updated by {}'.format(request.user.username)
                    )
                    
                    messages.success(request, 'Booking status updated to {}'.format(
                        dict(Inquiry.STATUS_CHOICES).get(new_status, new_status)
                    ))
                    return redirect('custom_admin_booking_detail', booking_id=booking.id)
                    
                except Exception as e:
                    logger.error("Error updating status for booking {}: {}".format(booking.id, str(e)))
                    messages.error(request, 'Error updating booking status.')
        
        elif action == 'assign_car':
            car_id = request.POST.get('car_id')
            if car_id:
                try:
                    # Verify car exists
                    car = get_object_or_404(Car, id=car_id)
                    
                    # Update assigned car using raw SQL
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE booking_inquiry 
                            SET assigned_car_id = %s, updated_at = NOW()
                            WHERE id = %s
                        """, [car_id, booking.id])
                    
                    messages.success(request, 'Car {} assigned to booking'.format(car.name))
                    return redirect('custom_admin_booking_detail', booking_id=booking.id)
                    
                except Exception as e:
                    logger.error("Error assigning car to booking {}: {}".format(booking.id, str(e)))
                    messages.error(request, 'Error assigning car to booking.')
        
        elif action == 'add_note':
            note = request.POST.get('admin_notes')
            if note:
                try:
                    # Update admin notes using raw SQL
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE booking_inquiry 
                            SET admin_notes = %s, updated_at = NOW()
                            WHERE id = %s
                        """, [note, booking.id])
                    
                    messages.success(request, 'Admin note added successfully')
                    return redirect('custom_admin_booking_detail', booking_id=booking.id)
                    
                except Exception as e:
                    logger.error("Error adding note to booking {}: {}".format(booking.id, str(e)))
                    messages.error(request, 'Error adding admin note.')
    
    # Get available cars of the same type using raw SQL
    available_cars = []
    if booking.car_type_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, registration_number, driver_name, driver_contact
                    FROM booking_car 
                    WHERE car_type_id = %s AND is_available = 1
                    ORDER BY name
                """, [booking.car_type_id])
                
                car_rows = cursor.fetchall()
                for row in car_rows:
                    available_cars.append({
                        'id': row[0],
                        'name': str(row[1]) if row[1] else '',
                        'registration_number': str(row[2]) if row[2] else '',
                        'driver_name': str(row[3]) if row[3] else '',
                        'driver_contact': str(row[4]) if row[4] else '',
                    })
                    
        except Exception as e:
            logger.error("Error loading available cars: {}".format(str(e)))
            available_cars = []
    
    # Get status history using raw SQL
    status_history = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT old_status, new_status, changed_by, changed_at, notes
                FROM booking_bookingstatushistory 
                WHERE inquiry_id = %s
                ORDER BY changed_at DESC
            """, [booking.id])
            
            history_rows = cursor.fetchall()
            for row in history_rows:
                status_history.append({
                    'old_status': str(row[0]) if row[0] else '',
                    'new_status': str(row[1]) if row[1] else '',
                    'changed_by': str(row[2]) if row[2] else '',
                    'changed_at': row[3],
                    'notes': str(row[4]) if row[4] else '',
                })
                
    except Exception as e:
        logger.error("Error loading status history: {}".format(str(e)))
        status_history = []
    
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
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.id, c.name, c.registration_number, c.is_available,
                    c.driver_name, c.driver_contact, ct.name as car_type_name, c.car_type_id, c.image
                FROM booking_car c
                JOIN booking_cartype ct ON c.car_type_id = ct.id
                ORDER BY ct.name, c.name, c.image
            """)
            cars = cursor.fetchall()
        
        # Get car types for the add form
        car_types = CarType.objects.all()
        # cars_obj = Car.objects.all()
        # cars = CarSerializer(cars_obj).data
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'add_car':
                name = request.POST.get('name')
                registration = request.POST.get('registration_number')
                car_type_id = request.POST.get('car_type')
                driver_name = request.POST.get('driver_name', '')
                driver_contact = request.POST.get('driver_contact', '')
                car_image = request.FILES.get('car_image')  # NEW LINE
                
                if name and registration and car_type_id:
                    car_type = get_object_or_404(CarType, id=car_type_id)
                    car = Car.objects.create(
                        name=name,
                        registration_number=registration,
                        car_type=car_type,
                        driver_name=driver_name,
                        driver_contact=driver_contact
                    )

                    # NEW: Handle image upload
                    if car_image:
                        try:
                            car.image = car_image
                            car.save()
                            logger.info(f"Image uploaded for car {car.id}: {car.image.name}")
                        except Exception as img_error:
                            logger.error(f"Error uploading image for car {car.id}: {str(img_error)}")
                            messages.warning(request, f"Car added successfully, but there was an issue with the image: {str(img_error)}")
                            return redirect('custom_admin_cars')
                        
                    messages.success(request, 'Car {} added successfully'.format(name))
                    return redirect('custom_admin_cars')
            
            elif action == 'edit_car':
                car_id = request.POST.get('car_id')
                name = request.POST.get('name', '').strip()
                registration_number = request.POST.get('registration_number', '').strip()
                is_available = request.POST.get('is_available') == 'on'
                driver_name = request.POST.get('driver_name', '').strip()
                driver_contact = request.POST.get('driver_contact', '').strip()
                car_type_id = request.POST.get('car_type_id')
                car_image = request.FILES.get('car_image')
                
                if car_id and name and registration_number and car_type_id:
                    try:
                        # Get the car object FIRST
                        car = Car.objects.get(id=car_id)
                        
                        # Update basic fields using Django ORM (not raw SQL)
                        car.name = name
                        car.registration_number = registration_number
                        car.is_available = is_available
                        car.driver_name = driver_name if driver_name else None
                        car.driver_contact = driver_contact if driver_contact else None
                        
                        # Update car type
                        try:
                            car_type = CarType.objects.get(id=car_type_id)
                            car.car_type = car_type
                        except CarType.DoesNotExist:
                            messages.error(request, 'Invalid car type selected.')
                            return redirect('custom_admin_cars')
                        
                        # Handle image upload
                        if car_image:
                            try:
                                # Delete old image if it exists
                                if car.image:
                                    try:
                                        default_storage.delete(car.image.name)
                                        logger.info(f"Old image deleted for car {car.id}")
                                    except Exception as delete_error:
                                        logger.warning(f"Could not delete old image: {str(delete_error)}")
                                
                                # Save new image
                                car.image = car_image
                                logger.info(f"New image assigned for car {car.id}: {car_image.name}")
                                
                            except Exception as img_error:
                                logger.error(f"Error handling image for car {car.id}: {str(img_error)}")
                                messages.error(request, f"Error uploading image: {str(img_error)}")
                                return redirect('custom_admin_cars')
                        
                        # Save all changes at once
                        car.save()
                        
                        messages.success(request, 'Car "{}" updated successfully!'.format(name))
                        logger.info(f"Car {car.id} updated successfully: {name}")
                        return redirect('custom_admin_cars')
                        
                    except Car.DoesNotExist:
                        messages.error(request, 'Car not found.')
                        logger.error(f"Car with ID {car_id} not found")
                    except Exception as e:
                        logger.error("Error updating car {}: {}".format(car_id, str(e)))
                        logger.error("Traceback: {}".format(traceback.format_exc()))
                        messages.error(request, 'Error updating car. Please try again.')
                else:
                    messages.error(request, 'Please fill in all required fields.')
        
        print(cars)
        context = {
            'cars': cars,
            'car_types': car_types,
        }
        
        return render(request, 'custom_admin/cars.html', context)
        
    except Exception as e:
        logger.error("Error in car list view: {}".format(str(e)))
        messages.error(request, 'An error occurred while loading the car list')
        return redirect('custom_admin_dashboard')


@login_required
@user_passes_test(is_admin_user)
def custom_admin_car_edit(request, car_id):
    """Admin view to edit car details"""
    try:
        # Get the car using raw SQL to avoid ORM issues
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.id, c.name, c.registration_number, c.is_available,
                    c.driver_name, c.driver_contact, c.car_type_id,
                    ct.name as car_type_name, ct.rate_per_km
                FROM booking_car c
                JOIN booking_cartype ct ON c.car_type_id = ct.id
                WHERE c.id = %s
            """, [car_id])
            
            car_data = cursor.fetchone()
            
            if not car_data:
                messages.error(request, 'Car not found')
                return redirect('custom_admin_cars')
            
            # Get all car types for the dropdown
            cursor.execute("SELECT id, name, rate_per_km FROM booking_cartype ORDER BY name")
            car_types = cursor.fetchall()
        
        if request.method == 'POST':
            # Handle form submission
            name = request.POST.get('name', '').strip()
            registration_number = request.POST.get('registration_number', '').strip()
            is_available = request.POST.get('is_available') == 'on'
            driver_name = request.POST.get('driver_name', '').strip()
            driver_contact = request.POST.get('driver_contact', '').strip()
            car_type_id = request.POST.get('car_type_id')
            
            # Validation
            if not name:
                messages.error(request, 'Car name is required')
            elif not registration_number:
                messages.error(request, 'Registration number is required')
            elif not car_type_id:
                messages.error(request, 'Car type is required')
            else:
                try:
                    # Update the car
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE booking_car 
                            SET name = %s, registration_number = %s, is_available = %s,
                                driver_name = %s, driver_contact = %s, car_type_id = %s
                            WHERE id = %s
                        """, [name, registration_number, is_available, driver_name, driver_contact, car_type_id, car_id])
                    
                    messages.success(request, 'Car "{}" updated successfully!'.format(name))
                    return redirect('custom_admin_cars')
                    
                except Exception as e:
                    logger.error("Error updating car {}: {}".format(car_id, str(e)))
                    messages.error(request, 'Error updating car. Please try again.')
        
        # Prepare context for template
        context = {
            'car': {
                'id': car_data[0],
                'name': car_data[1],
                'registration_number': car_data[2],
                'is_available': car_data[3],
                'driver_name': car_data[4],
                'driver_contact': car_data[5],
                'car_type_id': car_data[6],
                'car_type_name': car_data[7],
                'rate_per_km': car_data[8]
            },
            'car_types': [{'id': ct[0], 'name': ct[1], 'rate_per_km': ct[2]} for ct in car_types],
            'page_title': 'Edit Car'
        }
        
        return render(request, 'custom_admin/car_edit.html', context)
        
    except Exception as e:
        logger.error("Error in car edit view: {}".format(str(e)))
        messages.error(request, 'An error occurred while loading the car details')
        return redirect('custom_admin_cars')


@login_required
@user_passes_test(is_admin_user)
def custom_admin_routes(request):
    """Custom admin popular routes management - FIXED SQL PARAMETERS"""
    routes = []
    
    try:
        # Use raw SQL to bypass Django ORM decimal issues
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, origin, destination, distance_km, rate, is_active, created_at
                FROM booking_popularroute 
                ORDER BY origin, destination
            """)
            
            raw_routes = cursor.fetchall()
            
            for row in raw_routes:
                try:
                    route_data = {
                        'id': row[0],
                        'origin': row[1] or '',
                        'destination': row[2] or '',
                        'distance_km': float(row[3]) if row[3] is not None else None,
                        'rate': float(row[4]) if row[4] is not None else None,
                        'is_active': bool(row[5]),
                        'created_at': row[6],
                    }
                    routes.append(route_data)
                except Exception as route_error:
                    logger.error("Error processing route {}: {}".format(row[0], str(route_error)))
                    continue
            
        logger.info("Successfully loaded {} routes using raw SQL".format(len(routes)))
            
    except Exception as e:
        logger.error("Error loading routes: {}".format(str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        messages.error(request, 'Error loading routes. Please check the server logs.')
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
                    # Validate numeric values
                    rate_float = float(rate)
                    distance_float = float(distance)
                    
                    if rate_float <= 0 or distance_float <= 0:
                        messages.error(request, 'Rate and distance must be positive numbers.')
                        return redirect('custom_admin_routes')
                    
                    # Insert using raw SQL - FIXED: Use %s for Django/MySQL compatibility
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO booking_popularroute 
                            (origin, destination, rate, distance_km, is_active, created_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """, [origin, destination, rate_float, distance_float, True])
                    
                    messages.success(request, 'Route {} → {} added successfully'.format(origin, destination))
                    logger.info("Route added successfully: {} → {}".format(origin, destination))
                    
                except ValueError:
                    messages.error(request, 'Invalid rate or distance value. Please enter valid numbers.')
                except Exception as e:
                    messages.error(request, 'Error adding route: {}'.format(str(e)))
                    logger.error("Error creating route: {}".format(str(e)))
            else:
                messages.error(request, 'Please fill in all required fields.')
                
            return redirect('custom_admin_routes')
        
        elif action == 'update_route':
            route_id = request.POST.get('route_id')
            origin = request.POST.get('origin', '').strip()
            destination = request.POST.get('destination', '').strip()
            rate = request.POST.get('rate', '').strip()
            distance = request.POST.get('distance_km', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            
            if route_id and origin and destination and rate and distance:
                try:
                    rate_float = float(rate)
                    distance_float = float(distance)
                    
                    if rate_float <= 0 or distance_float <= 0:
                        messages.error(request, 'Rate and distance must be positive numbers.')
                        return redirect('custom_admin_routes')
                    
                    # Update using raw SQL - FIXED: Use %s placeholders consistently
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE booking_popularroute 
                            SET origin = %s, destination = %s, rate = %s, distance_km = %s, is_active = %s
                            WHERE id = %s
                        """, [origin, destination, rate_float, distance_float, is_active, route_id])
                    
                    messages.success(request, 'Route {} → {} updated successfully'.format(origin, destination))
                    logger.info("Route updated successfully: {} → {}".format(origin, destination))
                    return redirect('custom_admin_routes')
                    
                except ValueError:
                    messages.error(request, 'Invalid rate or distance value.')
                except Exception as e:
                    messages.error(request, 'Error updating route: {}'.format(str(e)))
                    logger.error("Error updating route {}: {}".format(route_id, str(e)))
            else:
                messages.error(request, 'Please fill in all required fields.')
                
            return redirect('custom_admin_routes')
        
        elif action == 'delete_route':
            route_id = request.POST.get('route_id')
            
            if route_id:
                try:
                    # Delete using raw SQL - FIXED: Use %s placeholder
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM booking_popularroute WHERE id = %s", [route_id])
                    
                    messages.success(request, 'Route deleted successfully')
                    logger.info("Route deleted successfully: ID {}".format(route_id))
                    return redirect('custom_admin_routes')
                    
                except Exception as e:
                    messages.error(request, 'Error deleting route: {}'.format(str(e)))
                    logger.error("Error deleting route {}: {}".format(route_id, str(e)))
            else:
                messages.error(request, 'Route ID is required for deletion.')
                
            return redirect('custom_admin_routes')
    
    context = {
        'routes': routes,
    }
    
    return render(request, 'custom_admin/routes.html', context)


@login_required
@user_passes_test(is_admin_user)
def custom_admin_route_edit(request, route_id):
    """Edit a specific route"""
    try:
        # Get route using raw SQL to avoid decimal issues
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, origin, destination, distance_km, rate, is_active
                FROM booking_popularroute 
                WHERE id = %s
            """, [route_id])
            
            route_data = cursor.fetchone()
            
            if not route_data:
                messages.error(request, 'Route not found.')
                return redirect('custom_admin_routes')
            
            route = {
                'id': route_data[0],
                'origin': route_data[1],
                'destination': route_data[2],
                'distance_km': float(route_data[3]) if route_data[3] else 0,
                'rate': float(route_data[4]) if route_data[4] else 0,
                'is_active': bool(route_data[5])
            }
    
    except Exception as e:
        logger.error("Error fetching route {}: {}".format(route_id, str(e)))
        messages.error(request, 'Error loading route data.')
        return redirect('custom_admin_routes')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_route':
            origin = request.POST.get('origin', '').strip()
            destination = request.POST.get('destination', '').strip()
            rate = request.POST.get('rate', '').strip()
            distance = request.POST.get('distance_km', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            
            if origin and destination and rate and distance:
                try:
                    rate_float = float(rate)
                    distance_float = float(distance)
                    
                    if rate_float <= 0 or distance_float <= 0:
                        messages.error(request, 'Rate and distance must be positive numbers.')
                        return render(request, 'custom_admin/route_edit.html', {'route': route})
                    
                    # Update using raw SQL - FIXED: Use %s placeholder
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE booking_popularroute 
                            SET origin = %s, destination = %s, rate = %s, distance_km = %s, is_active = %s
                            WHERE id = %s
                        """, [origin, destination, rate_float, distance_float, is_active, route_id])
                    
                    messages.success(request, 'Route {} → {} updated successfully'.format(origin, destination))
                    return redirect('custom_admin_routes')
                    
                except ValueError:
                    messages.error(request, 'Invalid rate or distance value.')
                except Exception as e:
                    messages.error(request, 'Error updating route: {}'.format(str(e)))
                    logger.error("Error updating route {}: {}".format(route_id, str(e)))
            else:
                messages.error(request, 'Please fill in all required fields.')
        
        elif action == 'delete_route':
            try:
                # Delete using raw SQL - FIXED: Use %s placeholder
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM booking_popularroute WHERE id = %s", [route_id])
                
                messages.success(request, 'Route deleted successfully')
                return redirect('custom_admin_routes')
                
            except Exception as e:
                messages.error(request, 'Error deleting route: {}'.format(str(e)))
                logger.error("Error deleting route {}: {}".format(route_id, str(e)))
    
    context = {
        'route': route,
    }
    
    return render(request, 'custom_admin/route_edit.html', context)


# ✅ API VIEWS (keeping all your existing API functions)
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
            logger.info("📥 Received booking data: {}".format(request.data))
            
            # Validate the incoming data
            serializer = BookingCreateSerializer(data=request.data)
            if serializer.is_valid():
                logger.info("✅ Serializer validation passed")
                
                # Try to create the inquiry
                try:
                    inquiry = serializer.save()
                    logger.info("✅ Booking created successfully: {}".format(inquiry.booking_id))
                    
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
                    logger.error("❌ Error saving inquiry: {}".format(str(save_error)))
                    logger.error("❌ Traceback: {}".format(traceback.format_exc()))
                    
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
                logger.error("❌ Validation errors: {}".format(serializer.errors))
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error("❌ Unexpected error creating booking: {}".format(str(e)))
            logger.error("❌ Traceback: {}".format(traceback.format_exc()))
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


# Legacy API endpoint for backward compatibility
@method_decorator(csrf_exempt, name='dispatch')
class BookingAPIView(View):
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            logger.info("Legacy API - Received booking data: {}".format(data))
            
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
            logger.error("Legacy API error: {}".format(str(e)))
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# ✅ CAR INTEGRATION VIEWS - UPDATED WITH EDIT FUNCTIONALITY

def get_cars_data():
    """Get cars data consistently using raw SQL to avoid ORM issues"""
    cars = []
    
    try:
        # with connection.cursor() as cursor:
        #     cursor.execute("""
        #         SELECT 
        #             c.id,
        #             c.name,
        #             c.registration_number,
        #             c.is_available,
        #             c.driver_name,
        #             c.driver_contact,
                    
        #             ct.name as car_type_name,
        #             ct.rate_per_km
        #         FROM booking_car c
        #         JOIN booking_cartype ct ON c.car_type_id = ct.id
        #         ORDER BY ct.name, c.name
        #     """)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.id,
                    c.name,
                    c.registration_number,
                    c.is_available,
                    c.driver_name,
                    c.driver_contact,
                    ct.name as car_type_name,
                    ct.rate_per_km,
                    c.image
                FROM booking_car c
                JOIN booking_cartype ct ON c.car_type_id = ct.id
                ORDER BY ct.name, c.name
            """)
            # cars = cursor.fetchall()
            raw_cars = cursor.fetchall()
            
            for row in raw_cars:
                try:
                    print(row)
                    car_data = {
                        'id': row[0],
                        'name': str(row[1]) if row[1] else 'Unknown Car',
                        'registration_number': str(row[2]) if row[2] else '',
                        'is_available': bool(row[3]),
                        'driver_name': str(row[4]) if row[4] else '',
                        'driver_contact': str(row[5]) if row[5] else '',
                        'car_type': {
                            'name': str(row[6]) if row[6] else 'Unknown',
                            'rate_per_km': float(row[7]) if row[7] else 0
                        },
                        'image': str(row[-1])
                    }
                    cars.append(car_data)
                except Exception as car_error:
                    logger.error("Error processing car {}: {}".format(row[0], str(car_error)))
                    continue
                    
    except Exception as e:
        logger.error("Error loading cars: {}".format(str(e)))
        cars = []
    
    return cars


def our_cars(request):
    """Our Cars page view - displays all available cars from the database"""
    cars = get_cars_data()
    
    context = {
        'cars': cars,
        'page_title': 'Our Fleet',
        'page_description': 'Choose from our diverse range of well-maintained, luxury vehicles'
    }
    
    return render(request, 'our-cars.html', context)


@csrf_exempt
def car_availability_check(request):
    """API endpoint to check real-time car availability"""
    if request.method == 'GET':
        car_id = request.GET.get('car_id')
        
        if not car_id:
            return JsonResponse({'error': 'car_id parameter required'}, status=400)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT c.is_available, c.name, ct.name as car_type
                    FROM booking_car c
                    JOIN booking_cartype ct ON c.car_type_id = ct.id
                    WHERE c.id = %s
                """, [car_id])
                
                result = cursor.fetchone()
                
                if result:
                    return JsonResponse({
                        'success': True,
                        'available': bool(result[0]),
                        'car_name': str(result[1]),
                        'car_type': str(result[2])
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Car not found'
                    }, status=404)
                    
        except Exception as e:
            logger.error("Error checking car availability: {}".format(str(e)))
            return JsonResponse({
                'success': False,
                'error': 'Database error'
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def car_specific_booking(request):
    """API endpoint for car-specific booking requests"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract car-specific data
            car_id = data.get('car_id')
            car_name = data.get('car_name', '')
            car_type = data.get('car_type', '').lower()
            
            # Validate car availability if specific car requested
            if car_id:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT is_available, name 
                        FROM booking_car 
                        WHERE id = %s
                    """, [car_id])
                    
                    car_result = cursor.fetchone()
                    
                    if not car_result:
                        return JsonResponse({
                            'success': False,
                            'error': 'Requested car not found'
                        }, status=404)
                    
                    if not car_result[0]:  # Car not available
                        return JsonResponse({
                            'success': False,
                            'error': 'Car {} is currently not available'.format(car_result[1])
                        }, status=400)
            
            # Prepare booking data for existing booking system
            booking_data = {
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'tripType': data.get('trip_type', 'one-way'),
                'pickupLocation': data.get('pickup_location'),
                'dropoffLocation': data.get('dropoff_location'),
                'pickupDate': data.get('pickup_date'),
                'dropoffDate': data.get('dropoff_date'),
                'carType': car_type or 'sedan',
                'totalPrice': data.get('estimated_price', 0),
                'distance': data.get('estimated_distance', 0),
                'specialRequests': "Specific car requested: {}".format(car_name) if car_name else data.get('special_requests', '')
            }
            
            # Use existing booking creation logic
            serializer = BookingCreateSerializer(data=booking_data)
            if serializer.is_valid():
                inquiry = serializer.save()
                
                # Assign specific car if requested
                if car_id:
                    try:
                        car = Car.objects.get(id=car_id)
                        inquiry.assigned_car = car
                        inquiry.save()
                        logger.info("Car {} assigned to booking {}".format(car.name, inquiry.booking_id))
                    except Car.DoesNotExist:
                        logger.warning("Car with ID {} not found for assignment".format(car_id))
                
                return JsonResponse({
                    'success': True,
                    'message': 'Booking request submitted successfully',
                    'booking_id': inquiry.booking_id,
                    'assigned_car': car_name if car_id else None
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error("Error creating car-specific booking: {}".format(str(e)))
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while processing your booking'
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
