import json
import logging
import traceback
import decimal
import random
import string
import io
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404, FileResponse, HttpResponseNotFound
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Case, When, DecimalField, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import require_http_methods, require_GET
from decimal import Decimal, InvalidOperation
from .models import Inquiry, CarType, Car, PopularRoute, BookingStatusHistory, Gallery
from .serializers import InquirySerializer, BookingCreateSerializer, CarSerializer

logger = logging.getLogger(__name__)

def is_admin_user(user):
    """Check if user is admin (superuser or staff)"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@require_GET
def get_available_cars_by_type(request):
    """
    API to return available cars grouped by car type.
    Response format:
    {
        "success": true,
        "data": {
            "Hatchback": ["Car A", "Car B"],
            "Sedan": ["Car C"],
            "SUV": []
        }
    }
    """
    try:
        car_types = CarType.objects.all()
        data = {}
        for ct in car_types:
            available_cars = ct.cars.filter(is_available=True).values_list("name", flat=True)
            data[ct.name] = list(available_cars)
        
        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def serve_gallery_image(request, gallery_id):
    """Serve gallery image from database BLOB storage"""
    try:
        gallery_item = get_object_or_404(Gallery, id=gallery_id, is_active=True)
        
        if not gallery_item.image_data:
            raise Http404("Image not found")
        
        content_type = gallery_item.image_content_type or 'image/jpeg'
        
        # Ensure proper content type format
        if not content_type.startswith('image/'):
            content_type = 'image/jpeg'
        
        response = HttpResponse(gallery_item.image_data, content_type=content_type)
        
        filename = gallery_item.image_filename or f'gallery_image_{gallery_id}.jpg'
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        response['Cache-Control'] = 'public, max-age=3600'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        response['Content-Length'] = len(gallery_item.image_data)
        
        return response
        
    except Gallery.DoesNotExist:
        raise Http404("Gallery item not found")
    except Exception as e:
        logger.error("Error serving gallery image {}: {}".format(gallery_id, str(e)))
        raise Http404("Error loading image")

from django.http import FileResponse, Http404
import io
import logging

logger = logging.getLogger(__name__)

def serve_gallery_video(request, gallery_id):
    """Serve gallery video from database BLOB storage with streaming"""
    try:
        gallery_item = get_object_or_404(Gallery, id=gallery_id, is_active=True)

        if not gallery_item.video_data:
            raise Http404("Video not found")

        content_type = gallery_item.video_content_type or 'video/mp4'
        if not content_type.startswith('video/'):
            content_type = 'video/mp4'

        # Wrap binary blob in BytesIO for streaming
        video_stream = io.BytesIO(gallery_item.video_data)
        filename = gallery_item.video_filename or f'gallery_video_{gallery_id}.mp4'

        response = FileResponse(video_stream, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Cache-Control'] = 'public, max-age=3600'
        response['Access-Control-Allow-Origin'] = '*'
        response['Content-Length'] = len(gallery_item.video_data)

        return response

    except Exception as e:
        logger.error(f"Error serving gallery video {gallery_id}: {str(e)}")
        raise Http404("Error loading video")

def get_gallery_image_info(request):
    """API endpoint to get gallery information in JSON format"""
    try:
        gallery_items = Gallery.objects.filter(is_active=True).order_by('display_order', '-created_at')
        
        gallery_data = []
        for item in gallery_items:
            gallery_data.append({
                'id': item.id,
                'title': item.title,
                'description': item.description or '',
                'display_order': item.display_order,
                'image_url': '/api/images/gallery/{}/'.format(item.id),
                'created_at': item.created_at.isoformat() if item.created_at else None
            })
        
        return JsonResponse({
            'success': True,
            'gallery_items': gallery_data,
            'count': len(gallery_data)
        })
        
    except Exception as e:
        logger.error("Error getting gallery info: {}".format(str(e)))
        return JsonResponse({
            'success': False,
            'error': 'Error loading gallery information'
        }, status=500)

def get_gallery_data_api(request):
    """API endpoint to get gallery data for frontend consumption"""
    try:
        logger.info("Gallery API called - checking for active gallery items")
        
        gallery_items = Gallery.objects.filter(is_active=True).order_by('display_order', '-created_at')
        
        logger.info(f"Found {gallery_items.count()} active gallery items")
        
        gallery_data = []
        for item in gallery_items:
            logger.info(f"Processing gallery item: {item.id} - {item.title}")
            gallery_data.append({
                'id': item.id,
                'title': item.title,
                'description': item.description or '',
                'display_order': item.display_order,
                'image_url': '/api/images/gallery/{}/'.format(item.id),
                'image_filename': item.image_filename or 'gallery_image.jpg',
                'video_url': '/api/videos/gallery/{}/'.format(item.id) if item.video_data else None,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'is_active': item.is_active,
            })
        
        logger.info(f"Returning {len(gallery_data)} gallery items to frontend")
        
        return JsonResponse({
            'status': 'success',
            'data': gallery_data,
            'total_count': len(gallery_data)
        })
        
    except Exception as e:
        logger.error("Error in get_gallery_data_api: {}".format(str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        return JsonResponse({
            'status': 'error',
            'message': 'Error loading gallery data',
            'data': []
        }, status=500)

def gallery(request):
    """Gallery page view"""
    try:
        gallery_items = Gallery.objects.filter(is_active=True).order_by('display_order', '-created_at')
        logger.info("Successfully loaded {} active gallery items".format(gallery_items.count()))
    except Exception as e:
        logger.error("Error loading gallery items: {}".format(str(e)))
        gallery_items = []
    
    context = {
        'gallery_items': gallery_items,
    }
    
    return render(request, 'gallery.html', context)

@login_required
@user_passes_test(is_admin_user)
def custom_admin_gallery(request):
    """Custom admin gallery management"""
    try:
        # Get gallery items using ORM
        gallery_items = Gallery.objects.order_by('display_order', '-created_at')
        for item in gallery_items:
            item.is_video = True if item.video_data else False
        
        logger.info("Successfully loaded {} gallery items using ORM".format(gallery_items.count()))
            
    except Exception as e:
        logger.error("Error loading gallery items: {}".format(str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        messages.error(request, 'Error loading gallery items. Please check the server logs.')
        gallery_items = []
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_gallery_item':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            display_order = request.POST.get('display_order', '0').strip()
            is_active = request.POST.get('is_active') == 'on'
            gallery_file = request.FILES.get('image') or request.FILES.get('video_file')  # Can be image or video
            
            if title and gallery_file:
                try:
                    # Validate display order
                    display_order_int = int(display_order) if display_order else 0
                    
                    if display_order_int < 0:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'message': 'Display order cannot be negative.'})
                        messages.error(request, 'Display order cannot be negative.')
                        return redirect('custom_admin_gallery')
                    
                    # Create gallery item using ORM
                    gallery_item = Gallery.objects.create(
                        title=title,
                        description=description if description else None,
                        display_order=display_order_int,
                        is_active=is_active
                    )
                    
                    # Handle file upload (image or video)
                    content_type = gallery_file.content_type.lower()
                    if content_type.startswith('image/'):
                        gallery_item.set_image_from_file(gallery_file)
                        logger.info("Image uploaded for new gallery item {}".format(title))
                    elif content_type.startswith('video/'):
                        gallery_item.set_video_from_file(gallery_file)
                        logger.info("Video uploaded for new gallery item {}".format(title))
                    else:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'message': 'Unsupported file type. Please upload an image or video.'})
                        messages.error(request, 'Unsupported file type. Please upload an image or video.')
                    
                    gallery_item.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Gallery item "{}" added successfully'.format(title)})
                    
                    messages.success(request, 'Gallery item "{}" added successfully'.format(title))
                    logger.info("Gallery item added successfully: {}".format(title))
                    
                except ValueError:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Invalid display order value. Please enter a valid number.'})
                    messages.error(request, 'Invalid display order value. Please enter a valid number.')
                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Error adding gallery item: {}'.format(str(e))})
                    messages.error(request, 'Error adding gallery item: {}'.format(str(e)))
                    logger.error("Error creating gallery item: {}".format(str(e)))
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Please provide a title and select an image or video.'})
                messages.error(request, 'Please provide a title and select an image or video.')
                
            return redirect('custom_admin_gallery')
        
        elif action == 'edit_gallery_item':
            gallery_id = request.POST.get('gallery_id')
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            display_order = request.POST.get('display_order', '0').strip()
            is_active = request.POST.get('is_active') == 'on'
            gallery_file = request.FILES.get('image') or request.FILES.get('video_file')  # Can be image or video
            
            if gallery_id and title:
                try:
                    display_order_int = int(display_order) if display_order else 0
                    
                    if display_order_int < 0:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'message': 'Display order cannot be negative.'})
                        messages.error(request, 'Display order cannot be negative.')
                        return redirect('custom_admin_gallery')
                    
                    # Get and update gallery item using ORM
                    gallery_item = get_object_or_404(Gallery, id=gallery_id)
                    
                    # Update gallery item fields
                    gallery_item.title = title
                    gallery_item.description = description if description else None
                    gallery_item.display_order = display_order_int
                    gallery_item.is_active = is_active
                    
                    # Handle new file upload (image or video)
                    if gallery_file:
                        content_type = gallery_file.content_type.lower()
                        if content_type.startswith('image/'):
                            gallery_item.set_image_from_file(gallery_file)
                            # clear video fields
                            gallery_item.video_filename = None
                            gallery_item.video_content_type = None
                            gallery_item.video_data = None
                            logger.info("New image uploaded for gallery item {}".format(gallery_id))
                        elif content_type.startswith('video/'):
                            gallery_item.set_video_from_file(gallery_file)
                            # clear image fields
                            gallery_item.image_filename = None
                            gallery_item.image_content_type = None
                            gallery_item.image_data = None
                            logger.info("New video uploaded for gallery item {}".format(gallery_id))
                        else:
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({'success': False, 'message': 'Unsupported file type. Please upload an image or video.'})
                            messages.error(request, 'Unsupported file type. Please upload an image or video.')
                    
                    gallery_item.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Gallery item "{}" updated successfully'.format(title)})
                    
                    messages.success(request, 'Gallery item "{}" updated successfully'.format(title))
                    logger.info("Gallery item updated successfully: {}".format(title))
                    return redirect('custom_admin_gallery')
                    
                except ValueError:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Invalid display order value.'})
                    messages.error(request, 'Invalid display order value.')
                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Error updating gallery item: {}'.format(str(e))})
                    messages.error(request, 'Error updating gallery item: {}'.format(str(e)))
                    logger.error("Error updating gallery item {}: {}".format(gallery_id, str(e)))
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Please fill in all required fields.'})
                messages.error(request, 'Please fill in all required fields.')
                
            return redirect('custom_admin_gallery')
        
        elif action == 'delete_gallery_item':
            gallery_id = request.POST.get('gallery_id')
            
            if gallery_id:
                try:
                    # Get and delete gallery item using ORM
                    gallery_item = get_object_or_404(Gallery, id=gallery_id)
                    gallery_title = gallery_item.title
                    
                    # Delete the gallery item (images are stored in database, so no file cleanup needed)
                    gallery_item.delete()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Gallery item "{}" deleted successfully'.format(gallery_title)})
                    
                    messages.success(request, 'Gallery item "{}" deleted successfully'.format(gallery_title))
                    logger.info("Gallery item deleted successfully: {} - ID {}".format(gallery_title, gallery_id))
                    return redirect('custom_admin_gallery')
                    
                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Error deleting gallery item: {}'.format(str(e))})
                    messages.error(request, 'Error deleting gallery item: {}'.format(str(e)))
                    logger.error("Error deleting gallery item {}: {}".format(gallery_id, str(e)))
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Gallery item ID is required for deletion.'})
                messages.error(request, 'Gallery item ID is required for deletion.')
                
            return redirect('custom_admin_gallery')
        
        elif action == 'toggle_status':
            gallery_id = request.POST.get('gallery_id')
            new_status = request.POST.get('new_status')
            
            if gallery_id and new_status:
                try:
                    # Get gallery item using ORM
                    gallery_item = get_object_or_404(Gallery, id=gallery_id)
                    
                    # Update status
                    gallery_item.is_active = new_status.lower() == 'true'
                    gallery_item.save(update_fields=['is_active'])
                    
                    status_text = 'activated' if gallery_item.is_active else 'deactivated'
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Gallery item "{}" {} successfully'.format(gallery_item.title, status_text)})
                    
                    messages.success(request, 'Gallery item "{}" {} successfully'.format(gallery_item.title, status_text))
                    logger.info("Gallery item {} {}: {}".format(gallery_item.title, status_text, gallery_id))
                    return redirect('custom_admin_gallery')
                    
                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': 'Error updating gallery item status: {}'.format(str(e))})
                    messages.error(request, 'Error updating gallery item status: {}'.format(str(e)))
                    logger.error("Error toggling status for gallery item {}: {}".format(gallery_id, str(e)))
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Invalid request parameters.'})
                messages.error(request, 'Invalid request parameters.')
                
            return redirect('custom_admin_gallery')
    
    context = {
        'gallery_items': gallery_items,
    }
    
    return render(request, 'custom_admin/gallery.html', context)

# API endpoint to get dynamic car types and rates with cache prevention
@require_http_methods(["GET"])
@never_cache
def get_car_types_api(request):
    """API endpoint to get car types with current rates for frontend - UPDATED WITH MIN/MAX RATES"""
    try:
        logger.info("🚗 Fetching car types from database...")
        
        # Get active car types with their current rates
        car_types = CarType.objects.filter(is_active=True).order_by('name')
        
        car_types_data = []
        for car_type in car_types:
            car_types_data.append({
                'id': car_type.id,
                'name': car_type.name.lower(),
                'display_name': car_type.name,
                'rate_per_km': float(car_type.rate_per_km),
                'minimum_rate_per_km': float(car_type.minimum_rate_per_km),
                'maximum_rate_per_km': float(car_type.maximum_rate_per_km),
                'minimum_distance_cap': float(car_type.minimum_distance_cap),
                'is_active': car_type.is_active
            })
        
        logger.info(f"✅ Returning {len(car_types_data)} car types with rates")
        
        response = JsonResponse({
            'success': True,
            'car_types': car_types_data,
            'timestamp': timezone.now().isoformat()
        })
        
        # Prevent caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error fetching car types: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error fetching car types',
            'car_types': []
        }, status=500)

# Image serving views for BLOB storage with better error handling
@require_http_methods(["GET"])
@cache_control(max_age=3600)  # Cache for 1 hour
def serve_car_image(request, car_id):
    """Serve car image from database BLOB storage"""
    try:
        car = get_object_or_404(Car, id=car_id)
        
        if not car.image_data:
            logger.warning(f"No image data found for car {car_id}")
            raise Http404("Car image not found")
        
        # Create HTTP response with image data
        response = HttpResponse(
            car.image_data,
            content_type=car.image_content_type or 'image/jpeg'
        )
        
        # Add filename for download if available
        if car.image_filename:
            response['Content-Disposition'] = f'inline; filename="{car.image_filename}"'
        
        # Add cache headers
        response['Cache-Control'] = 'public, max-age=3600'
        response['Access-Control-Allow-Origin'] = '*'
        
        logger.info(f"✅ Successfully served car image {car_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error serving car image {car_id}: {str(e)}")
        raise Http404("Error loading car image")


@require_http_methods(["GET"])
@cache_control(max_age=3600)  # Cache for 1 hour
def serve_route_image(request, route_id):
    """Serve route image from database BLOB storage - FIXED VERSION"""
    try:
        route = get_object_or_404(PopularRoute, id=route_id)
        
        if not route.image_data:
            logger.warning(f"No image data found for route {route_id}")
            # ✅ FIXED: Try to check if file-based image exists as fallback
            if route.image and hasattr(route.image, 'path'):
                try:
                    with open(route.image.path, 'rb') as f:
                        image_data = f.read()
                    response = HttpResponse(
                        image_data,
                        content_type='image/jpeg'
                    )
                    response['Cache-Control'] = 'public, max-age=3600'
                    response['Access-Control-Allow-Origin'] = '*'
                    logger.info(f"✅ Served route image {route_id} from file fallback")
                    return response
                except Exception as file_error:
                    logger.error(f"❌ File fallback failed for route {route_id}: {str(file_error)}")
            
            raise Http404("Route image not found")
        
        # Create HTTP response with image data
        response = HttpResponse(
            route.image_data,
            content_type=route.image_content_type or 'image/jpeg'
        )
        
        # Add filename for download if available
        if route.image_filename:
            response['Content-Disposition'] = f'inline; filename="{route.image_filename}"'
        
        # ✅ FIXED: Add proper headers
        response['Cache-Control'] = 'public, max-age=3600'
        response['Access-Control-Allow-Origin'] = '*'  # Add CORS header
        response['Content-Length'] = len(route.image_data)  # Add content length
        
        logger.info(f"✅ Successfully served route image {route_id} from BLOB storage")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error serving route image {route_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise Http404("Error loading route image")


@require_http_methods(["GET"])
def get_car_image_info(request, car_id):
    """Get car image metadata as JSON"""
    try:
        car = get_object_or_404(Car, id=car_id)
        
        return JsonResponse({
            'success': True,
            'has_image': car.has_image,
            'image_url': car.image_url,
            'filename': car.image_filename,
            'content_type': car.image_content_type,
            'size': len(car.image_data) if car.image_data else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting car image info {car_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Car not found or error loading image info'
        }, status=404)


@require_http_methods(["GET"])
def get_route_image_info(request, route_id):
    """Get route image metadata as JSON - FIXED VERSION"""
    try:
        route = get_object_or_404(PopularRoute, id=route_id)
        
        # ✅ FIXED: Better image URL determination
        image_url = None
        has_image = False
        
        if route.image_data:
            image_url = f"/api/images/route/{route.id}/"
            has_image = True
        elif route.image and hasattr(route.image, 'url'):
            try:
                image_url = route.image.url
                has_image = True
            except:
                pass
        
        return JsonResponse({
            'success': True,
            'has_image': has_image,
            'image_url': image_url,
            'filename': route.image_filename,
            'content_type': route.image_content_type,
            'size': len(route.image_data) if route.image_data else 0,
            'route_id': route.id,
            'origin': route.origin,
            'destination': route.destination
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting route image info {route_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Route not found or error loading image info'
        }, status=404)


def safe_decimal_convert(value, default=0.0):
    """Safely convert any value to float, handling decimal errors"""
    if value is None:
        return default
    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, str):
            return float(Decimal(value))
        else:
            return default
    except (InvalidOperation, ValueError, TypeError, decimal.InvalidOperation):
        logger.warning("Could not convert value {} to decimal, using default {}".format(value, default))
        return default

def get_routes_data():
    """Get routes data consistently for all views - FIXED FOR BLOB STORAGE"""
    routes = []
    
    try:
        # Use ORM with safe decimal handling
        popular_routes = PopularRoute.objects.filter(is_active=True).order_by('origin', 'destination')
        
        for route in popular_routes:
            try:
                # ✅ FIXED: Better image URL determination with proper fallback
                image_url = ''
                has_image = False
                
                if route.image_data:
                    # Use database BLOB URL
                    image_url = f"/api/images/route/{route.id}/"
                    has_image = True
                    logger.debug(f"Route {route.id}: Using BLOB image URL: {image_url}")
                elif route.image and hasattr(route.image, 'url'):
                    try:
                        # Use file-based URL (legacy)
                        image_url = route.image.url
                        has_image = True
                        logger.debug(f"Route {route.id}: Using file image URL: {image_url}")
                    except Exception as img_error:
                        logger.warning(f"Route {route.id}: File image URL error: {str(img_error)}")
                        image_url = ''
                        has_image = False
                else:
                    # No image available
                    logger.debug(f"Route {route.id}: No image available")
                    image_url = ''
                    has_image = False
                
                route_data = {
                    'id': route.id,
                    'origin': str(route.origin) if route.origin else '',
                    'destination': str(route.destination) if route.destination else '',
                    'distance_km': safe_decimal_convert(route.distance_km),
                    'rate': safe_decimal_convert(route.rate),
                    'image': image_url,  # ✅ FIXED: Use proper image URL
                    'image_url': image_url,  # ✅ FIXED: Add image_url field
                    'has_image': has_image,  # ✅ FIXED: Boolean flag
                    'is_active': route.is_active,
                    'created_at': route.created_at,
                }
                routes.append(route_data)
                logger.debug(f"✅ Route {route.id} processed: {route.origin} → {route.destination}, has_image: {has_image}")
                
            except Exception as route_error:
                logger.error("❌ Error processing route {}: {}".format(route.id, str(route_error)))
                continue
                    
    except Exception as e:
        logger.error("❌ Error loading routes: {}".format(str(e)))
        routes = []
    
    logger.info(f"✅ Loaded {len(routes)} routes for display")
    return routes

def index(request):
    """Main homepage view"""
    routes = get_routes_data()[:8]  # Limit to 8 for homepage
    gallery_items = Gallery.objects.filter(is_active=True).order_by("display_order")[:6]
    
    context = {
        'routes': routes,
        'gallery_items':gallery_items
    }

    return render(request, "index.html", context)

def popular_routes(request):
    """Popular routes page view - USING ORM"""
    routes = get_routes_data()  # All routes for this page
    
    context = {
        'page_title': 'Popular Routes',
        'page_description': 'Explore our most requested intercity taxi services',
        'routes': routes,
    }
    
    return render(request, "popular-routes.html", context)

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
    """Custom admin dashboard - USING ORM WITH SAFE DECIMAL HANDLING"""
    try:
        # Get statistics using ORM (these don't involve decimal fields directly)
        total_bookings = Inquiry.objects.count()
        pending_bookings = Inquiry.objects.filter(status='pending').count()
        confirmed_bookings = Inquiry.objects.filter(status='confirmed').count()
        completed_bookings = Inquiry.objects.filter(status='completed').count()
        
        # Recent bookings - Use select_related to avoid N+1 queries
        recent_bookings = []
        try:
            # Get recent bookings with related data
            bookings_queryset = Inquiry.objects.select_related('car_type').order_by('-created_at')[:10]
            
            for booking in bookings_queryset:
                try:
                    # Create booking-like object for template compatibility with safe decimal handling
                    booking_obj = {
                        'id': booking.id,
                        'booking_id': str(booking.booking_id) if booking.booking_id else '',
                        'name': str(booking.name) if booking.name else '',
                        'email': str(booking.email) if booking.email else '',
                        'origin': str(booking.origin) if booking.origin else '',
                        'destination': str(booking.destination) if booking.destination else '',
                        'datetime': booking.datetime,
                        'status': str(booking.status) if booking.status else 'pending',
                        'price': booking.safe_price,  # Use safe property
                        'created_at': booking.created_at,
                        'get_status_display': booking.get_status_display(),
                        'detail_url': '/admin-panel/bookings/{}/'.format(booking.id)
                    }
                    recent_bookings.append(booking_obj)
                except Exception as booking_error:
                    logger.error("Error processing booking {}: {}".format(booking.id, str(booking_error)))
                    continue
                        
        except Exception as bookings_error:
            logger.error("Error loading recent bookings: {}".format(str(bookings_error)))
            recent_bookings = []
        
        # Monthly stats - Set to beginning of month
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_bookings = Inquiry.objects.filter(created_at__gte=current_month).count()
        
        # Safe revenue calculation using ORM aggregation with error handling
        monthly_revenue = 0
        try:
            # Use aggregate with Coalesce to handle NULL values
            revenue_result = Inquiry.objects.filter(
                created_at__gte=current_month,
                status__in=['confirmed', 'completed']
            ).aggregate(
                total_revenue=Coalesce(Sum('price'), Decimal('0.00'))
            )
            
            if revenue_result and revenue_result['total_revenue']:
                monthly_revenue = safe_decimal_convert(revenue_result['total_revenue'])
                
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
    """Custom admin bookings list - USING ORM WITH SAFE DECIMAL HANDLING"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        date_filter = request.GET.get('date_filter', '')
        
        # Build queryset with filters using ORM
        queryset = Inquiry.objects.select_related('car_type')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if search_query:
            queryset = queryset.filter(
                Q(booking_id__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(origin__icontains=search_query) |
                Q(destination__icontains=search_query)
            )
        
        if date_filter:
            today = timezone.now().date()
            if date_filter == 'today':
                queryset = queryset.filter(created_at__date=today)
            elif date_filter == 'week':
                week_ago = today - timedelta(days=7)
                queryset = queryset.filter(created_at__date__gte=week_ago)
            elif date_filter == 'month':
                month_ago = today - timedelta(days=30)
                queryset = queryset.filter(created_at__date__gte=month_ago)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Convert to safe booking objects to avoid decimal issues in templates
        safe_bookings = []
        try:
            for booking in queryset:
                try:
                    # Create a safe booking wrapper
                    class SafeBooking:
                        def __init__(self, booking_obj):
                            self.id = booking_obj.id
                            self.booking_id = booking_obj.booking_id
                            self.name = booking_obj.name
                            self.email = booking_obj.email
                            self.number = booking_obj.number
                            self.origin = booking_obj.origin
                            self.destination = booking_obj.destination
                            self.datetime = booking_obj.datetime
                            self.status = booking_obj.status
                            self.price = booking_obj.safe_price  # Use safe property
                            self.distance_km = booking_obj.safe_distance  # Use safe property
                            self.car_type = booking_obj.car_type
                            self.created_at = booking_obj.created_at
                        
                        def get_status_display(self):
                            return dict(Inquiry.STATUS_CHOICES).get(self.status, 'Unknown')
                    
                    safe_booking = SafeBooking(booking)
                    safe_bookings.append(safe_booking)
                    
                except Exception as booking_error:
                    logger.warning("Skipping booking {} due to error: {}".format(
                        booking.id, str(booking_error)
                    ))
                    continue
                    
        except Exception as queryset_error:
            logger.error("Error processing queryset: {}".format(str(queryset_error)))
            safe_bookings = []
        
        # Use Django's built-in Paginator with the safe bookings list
        paginator = Paginator(safe_bookings, 20)  # 20 bookings per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
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
        empty_paginator = Paginator([], 1)
        empty_page = empty_paginator.get_page(1)
        
        context = {
            'page_obj': empty_page,
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
    """Custom admin booking detail view - CONVERTED TO ORM WITH SAFE DECIMAL HANDLING"""
    try:
        # Get booking using ORM with select_related for efficiency
        booking = get_object_or_404(
            Inquiry.objects.select_related('car_type', 'assigned_car'), 
            id=booking_id
        )
        
        # Create a safe wrapper to avoid decimal issues in templates
        class SafeBookingDetail:
            def __init__(self, booking_obj):
                # Copy all attributes safely
                for field in booking_obj._meta.fields:
                    field_name = field.name
                    field_value = getattr(booking_obj, field_name)
                    
                    # Handle decimal fields specially
                    if field_name in ['price', 'distance_km'] and field_value is not None:
                        try:
                            setattr(self, field_name, safe_decimal_convert(field_value))
                        except:
                            setattr(self, field_name, 0.0)
                    else:
                        setattr(self, field_name, field_value)
                
                # Copy related objects
                self.car_type = booking_obj.car_type
                self.assigned_car = booking_obj.assigned_car
            
            def get_status_display(self):
                return dict(Inquiry.STATUS_CHOICES).get(self.status, 'Unknown')
            
            def get_trip_type_display(self):
                return dict(Inquiry.TRIP_CHOICES).get(self.trip_type, 'Unknown')
        
        safe_booking = SafeBookingDetail(booking)
            
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
            
            if new_status and new_status in dict(Inquiry.STATUS_CHOICES):
                try:
                    # Update status using ORM
                    booking.status = new_status
                    booking.save(update_fields=['status', 'updated_at'])
                    
                    # Create status history using ORM
                    try:
                        BookingStatusHistory.objects.create(
                            inquiry=booking,
                            old_status=old_status,
                            new_status=new_status,
                            changed_by=request.user.username,
                            notes='Status updated by {}'.format(request.user.username)
                        )
                    except Exception as history_error:
                        logger.warning("Error creating status history: {}".format(str(history_error)))
                        # Don't fail the whole operation if history creation fails
                    
                    messages.success(request, 'Booking status updated from {} to {}'.format(
                        dict(Inquiry.STATUS_CHOICES).get(old_status, old_status),
                        dict(Inquiry.STATUS_CHOICES).get(new_status, new_status)
                    ))
                    return redirect('custom_admin_booking_detail', booking_id=booking.id)
                    
                except Exception as e:
                    logger.error("Error updating status for booking {}: {}".format(booking.id, str(e)))
                    logger.error("Traceback: {}".format(traceback.format_exc()))
                    messages.error(request, 'Error updating booking status: {}'.format(str(e)))
            else:
                messages.error(request, 'Invalid status selected.')
        
        elif action == 'assign_car':
            car_id = request.POST.get('car_id')
            if car_id:
                try:
                    # Get car using ORM
                    car = get_object_or_404(Car, id=car_id)
                    
                    # Update assigned car using ORM
                    booking.assigned_car = car
                    booking.save(update_fields=['assigned_car', 'updated_at'])
                    
                    messages.success(request, 'Car {} assigned to booking'.format(car.name))
                    return redirect('custom_admin_booking_detail', booking_id=booking.id)
                    
                except Exception as e:
                    logger.error("Error assigning car to booking {}: {}".format(booking.id, str(e)))
                    messages.error(request, 'Error assigning car to booking.')
        
        elif action == 'remove_car':
            try:
                # Get current assigned car name for success message
                car_name = None
                if booking.assigned_car:
                    car_name = booking.assigned_car.name
                
                # Remove assigned car using ORM
                booking.assigned_car = None
                booking.save(update_fields=['assigned_car', 'updated_at'])
                
                if car_name:
                    messages.success(request, 'Car {} removed from booking'.format(car_name))
                else:
                    messages.success(request, 'Car removed from booking')
                return redirect('custom_admin_booking_detail', booking_id=booking.id)
                
            except Exception as e:
                logger.error("Error removing car from booking {}: {}".format(booking.id, str(e)))
                messages.error(request, 'Error removing car from booking.')
        
        elif action == 'add_note':
            note = request.POST.get('admin_notes', '').strip()
            try:
                # Update admin notes using ORM
                booking.admin_notes = note
                booking.save(update_fields=['admin_notes', 'updated_at'])
                
                messages.success(request, 'Admin note updated successfully')
                return redirect('custom_admin_booking_detail', booking_id=booking.id)
                
            except Exception as e:
                logger.error("Error adding note to booking {}: {}".format(booking.id, str(e)))
                messages.error(request, 'Error updating admin note.')
    
    # Get available cars of the same type using ORM
    available_cars = []
    if booking.car_type_id:
        try:
            available_cars = Car.objects.filter(
                car_type_id=booking.car_type_id,
                is_available=True
            ).order_by('name')
                    
        except Exception as e:
            logger.error("Error loading available cars: {}".format(str(e)))
            available_cars = []
    
    # Get status history using ORM
    status_history = []
    try:
        status_history = BookingStatusHistory.objects.filter(
            inquiry=booking
        ).order_by('-changed_at')
                
    except Exception as e:
        logger.error("Error loading status history: {}".format(str(e)))
        status_history = []
    
    context = {
        'booking': safe_booking,  # Use safe booking wrapper
        'available_cars': available_cars,
        'status_history': status_history,
        'status_choices': Inquiry.STATUS_CHOICES,
    }
    
    return render(request, 'custom_admin/booking_detail.html', context)

@login_required
@user_passes_test(is_admin_user)
def custom_admin_cars(request):
    """Custom admin cars management - UPDATED FOR BLOB STORAGE WITH DELETE FUNCTIONALITY"""
    try:
        # Get cars using ORM and convert to tuple format for template compatibility
        car_objects = Car.objects.select_related('car_type').order_by('car_type__name', 'name')

        cars = []
        for car in car_objects:
            # ✅ FIXED: Check if car has BLOB image data first, then fallback to file
            if car.image_data:
                # Use database BLOB URL
                image_url = f"/api/images/car/{car.id}/"
            elif car.image and hasattr(car.image, 'url'):
                # Use file-based URL (legacy)
                image_url = car.image.url
            else:
                # No image available
                image_url = ''
            
            car_tuple = (
                car.id,                                    # car.0 - id
                car.name,                                  # car.1 - name  
                car.is_available,                          # car.2 - is_available (was car.3)
                car.car_type.name if car.car_type else 'Unknown',  # car.3 - car_type_name (was car.6)
                car.car_type.id if car.car_type else None, # car.4 - car_type_id (was car.7)
                image_url if image_url else '',            # car.5 - image_url (was car.8)
                bool(car.image_data) or bool(car.image),   # car.6 - has_image (was car.9)
            )
            cars.append(car_tuple)
        
        # Get car types for the add form using ORM
        car_types = CarType.objects.order_by('name')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'add_car':
                name = request.POST.get('name')
                car_type_id = request.POST.get('car_type')
                car_image = request.FILES.get('car_image')
                
                if name and car_type_id:
                    try:
                        # Verify car type exists using ORM
                        car_type = get_object_or_404(CarType, id=car_type_id)
                        
                        car = Car.objects.create(
                            name=name,
                            car_type=car_type,
                            is_available=True
                        )
                        
                        # ✅ UPDATED: Handle image upload to BLOB storage
                        if car_image:
                            car.set_image_from_file(car_image)
                            car.save()
                        
                        messages.success(request, 'Car {} added successfully'.format(name))
                        return redirect('custom_admin_cars')
                        
                    except Exception as e:
                        logger.error("Error adding car: {}".format(str(e)))
                        messages.error(request, 'Error adding car. Please try again.')
            
            elif action == 'edit_car':
                car_id = request.POST.get('car_id')
                name = request.POST.get('name', '').strip()
                is_available = request.POST.get('is_available') == 'on'
                car_type_id = request.POST.get('car_type_id')
                car_image = request.FILES.get('car_image')
                
                if car_id and name and car_type_id:
                    try:
                        # Get car and car type using ORM
                        car = get_object_or_404(Car, id=car_id)
                        car_type = get_object_or_404(CarType, id=car_type_id)
                        
                        car.name = name
                        car.is_available = is_available
                        car.car_type = car_type
                        
                        # ✅ UPDATED: Handle image upload to BLOB storage
                        if car_image:
                            car.set_image_from_file(car_image)
                            logger.info("New image uploaded for car {}".format(car_id))
                        
                        car.save()
                        
                        messages.success(request, 'Car "{}" updated successfully!'.format(name))
                        logger.info("Car {} updated successfully: {}".format(car_id, name))
                        return redirect('custom_admin_cars')
                        
                    except Exception as e:
                        logger.error("Error updating car {}: {}".format(car_id, str(e)))
                        logger.error("Traceback: {}".format(traceback.format_exc()))
                        messages.error(request, 'Error updating car. Please try again.')
                else:
                    messages.error(request, 'Please fill in all required fields.')
            
            # ✅ NEW: Delete car functionality
            elif action == 'delete_car':
                car_id = request.POST.get('car_id')
                
                if car_id:
                    try:
                        # Get and delete car using ORM
                        car = get_object_or_404(Car, id=car_id)
                        car_name = car.name
                        
                        # Check if car is assigned to any active bookings
                        active_bookings = Inquiry.objects.filter(
                            assigned_car=car,
                            status__in=['pending', 'confirmed', 'in_progress']
                        ).count()
                        
                        if active_bookings > 0:
                            messages.error(request, 'Cannot delete car "{}". It is assigned to {} active booking(s).'.format(
                                car_name, active_bookings))
                            return redirect('custom_admin_cars')
                        
                        # Delete the car (images are stored in database, so no file cleanup needed)
                        car.delete()
                        
                        messages.success(request, 'Car "{} deleted successfully'.format(car_name))
                        logger.info("Car deleted successfully: {} - ID {}".format(car_name, car_id))
                        return redirect('custom_admin_cars')
                        
                    except Exception as e:
                        messages.error(request, 'Error deleting car: {}'.format(str(e)))
                        logger.error("Error deleting car {}: {}".format(car_id, str(e)))
                else:
                    messages.error(request, 'Car ID is required for deletion.')
                    
                return redirect('custom_admin_cars')
        
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
    """Admin view to edit car details - CONVERTED TO ORM"""
    try:
        # Get the car using ORM
        car = get_object_or_404(Car.objects.select_related('car_type'), id=car_id)
        
        # Get all car types for the dropdown using ORM
        car_types = CarType.objects.order_by('name')
        
        if request.method == 'POST':
            # Handle form submission
            name = request.POST.get('name', '').strip()
            is_available = request.POST.get('is_available') == 'on'
            car_type_id = request.POST.get('car_type_id')
            
            if not name:
                messages.error(request, 'Car name is required')
            elif not car_type_id:
                messages.error(request, 'Car type is required')
            else:
                try:
                    # Get car type using ORM
                    car_type = get_object_or_404(CarType, id=car_type_id)
                    
                    car.name = name
                    car.is_available = is_available
                    car.car_type = car_type
                    car.save()
                    
                    messages.success(request, 'Car "{}" updated successfully!'.format(name))
                    return redirect('custom_admin_cars')
                    
                except Exception as e:
                    logger.error("Error updating car {}: {}".format(car_id, str(e)))
                    messages.error(request, 'Error updating car. Please try again.')
        
        context = {
            'car': car,
            'car_types': car_types,
            'page_title': 'Edit Car'
        }
        
        return render(request, 'custom_admin/car_edit.html', context)
        
    except Exception as e:
        logger.error("Error in car edit view: {}".format(str(e)))
        messages.error(request, 'An error occurred while loading the car details')
        return redirect('custom_admin_cars')


@login_required
@user_passes_test(is_admin_user)
def custom_admin_car_types(request):
    """Custom admin car types management - UPDATED WITH MIN/MAX RATES AND DELETE FUNCTIONALITY"""
    try:
        # Get car types using ORM
        car_types = CarType.objects.order_by('name')
        
        logger.info("Successfully loaded {} car types using ORM".format(car_types.count()))
            
    except Exception as e:
        logger.error("Error loading car types: {}".format(str(e)))
        logger.error("Traceback: {}".format(traceback.format_exc()))
        messages.error(request, 'Error loading car types. Please check the server logs.')
        car_types = []
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_car_type':
            name = request.POST.get('name', '').strip()
            rate_per_km = request.POST.get('rate_per_km', '').strip()
            minimum_rate_per_km = request.POST.get('minimum_rate_per_km', '').strip()  # ✅ NEW
            maximum_rate_per_km = request.POST.get('maximum_rate_per_km', '').strip()  # ✅ NEW
            minimum_distance_cap = request.POST.get('minimum_distance_cap', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            
            if name and rate_per_km and minimum_rate_per_km and maximum_rate_per_km:  # ✅ UPDATED validation
                try:
                    # Validate numeric values
                    rate_decimal = Decimal(rate_per_km)
                    min_rate_decimal = Decimal(minimum_rate_per_km)  # ✅ NEW
                    max_rate_decimal = Decimal(maximum_rate_per_km)  # ✅ NEW
                    min_distance_decimal = Decimal(minimum_distance_cap) if minimum_distance_cap else Decimal('0.00')
                    
                    if rate_decimal <= 0 or min_rate_decimal <= 0 or max_rate_decimal <= 0:  # ✅ UPDATED validation
                        messages.error(request, 'All rates must be positive numbers.')
                        return redirect('custom_admin_car_types')
                    
                    if min_rate_decimal > max_rate_decimal:  # ✅ NEW validation
                        messages.error(request, 'Minimum rate cannot be greater than maximum rate.')
                        return redirect('custom_admin_car_types')
                    
                    if min_distance_decimal < 0:
                        messages.error(request, 'Minimum distance cap cannot be negative.')
                        return redirect('custom_admin_car_types')
                    
                    # Check if car type already exists
                    if CarType.objects.filter(name__iexact=name).exists():
                        messages.error(request, 'Car type "{}" already exists.'.format(name))
                        return redirect('custom_admin_car_types')
                    
                    # Create car type using ORM - ✅ UPDATED with new fields
                    car_type = CarType.objects.create(
                        name=name,
                        rate_per_km=rate_decimal,
                        minimum_rate_per_km=min_rate_decimal,  # ✅ NEW
                        maximum_rate_per_km=max_rate_decimal,  # ✅ NEW
                        minimum_distance_cap=min_distance_decimal,
                        is_active=is_active
                    )
                    
                    messages.success(request, 'Car type "{}" added successfully with round-trip rate range ₹{}-₹{}/km'.format(
                        name, min_rate_decimal, max_rate_decimal))
                    logger.info("Car type added successfully: {}".format(name))
                    
                except (ValueError, InvalidOperation):
                    messages.error(request, 'Invalid rate or distance value. Please enter valid numbers.')
                except Exception as e:
                    messages.error(request, 'Error adding car type: {}'.format(str(e)))
                    logger.error("Error creating car type: {}".format(str(e)))
            else:
                messages.error(request, 'Please fill in all required fields including min/max rates.')
                
            return redirect('custom_admin_car_types')
        
        elif action == 'edit_car_type':
            car_type_id = request.POST.get('car_type_id')
            name = request.POST.get('name', '').strip()
            rate_per_km = request.POST.get('rate_per_km', '').strip()
            minimum_rate_per_km = request.POST.get('minimum_rate_per_km', '').strip()  # ✅ NEW
            maximum_rate_per_km = request.POST.get('maximum_rate_per_km', '').strip()  # ✅ NEW
            minimum_distance_cap = request.POST.get('minimum_distance_cap', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            
            if car_type_id and name and rate_per_km and minimum_rate_per_km and maximum_rate_per_km:  # ✅ UPDATED validation
                try:
                    rate_decimal = Decimal(rate_per_km)
                    min_rate_decimal = Decimal(minimum_rate_per_km)  # ✅ NEW
                    max_rate_decimal = Decimal(maximum_rate_per_km)  # ✅ NEW
                    min_distance_decimal = Decimal(minimum_distance_cap) if minimum_distance_cap else Decimal('0.00')
                    
                    if rate_decimal <= 0 or min_rate_decimal <= 0 or max_rate_decimal <= 0:  # ✅ UPDATED validation
                        messages.error(request, 'All rates must be positive numbers.')
                        return redirect('custom_admin_car_types')
                    
                    if min_rate_decimal > max_rate_decimal:  # ✅ NEW validation
                        messages.error(request, 'Minimum rate cannot be greater than maximum rate.')
                        return redirect('custom_admin_car_types')
                    
                    if min_distance_decimal < 0:
                        messages.error(request, 'Minimum distance cap cannot be negative.')
                        return redirect('custom_admin_car_types')
                    
                    # Get and update car type using ORM
                    car_type = get_object_or_404(CarType, id=car_type_id)
                    
                    # Check if name already exists for other car types
                    existing_car_type = CarType.objects.filter(name__iexact=name).exclude(id=car_type_id).first()
                    if existing_car_type:
                        messages.error(request, 'Car type "{}" already exists.'.format(name))
                        return redirect('custom_admin_car_types')
                    
                    # Update car type using ORM - ✅ UPDATED with new fields
                    car_type.name = name
                    car_type.rate_per_km = rate_decimal
                    car_type.minimum_rate_per_km = min_rate_decimal  # ✅ NEW
                    car_type.maximum_rate_per_km = max_rate_decimal  # ✅ NEW
                    car_type.minimum_distance_cap = min_distance_decimal
                    car_type.is_active = is_active
                    car_type.save()
                    
                    messages.success(request, 'Car type "{}" updated successfully with round-trip rate range ₹{}-₹{}/km'.format(
                        name, min_rate_decimal, max_rate_decimal))
                    logger.info("Car type updated successfully: {}".format(name))
                    return redirect('custom_admin_car_types')
                    
                except (ValueError, InvalidOperation):
                    messages.error(request, 'Invalid rate or distance value.')
                except Exception as e:
                    messages.error(request, 'Error updating car type: {}'.format(str(e)))
                    logger.error("Error updating car type {}: {}".format(car_type_id, str(e)))
            else:
                messages.error(request, 'Please fill in all required fields including min/max rates.')
                
            return redirect('custom_admin_car_types')
        
        # ✅ NEW: Delete car type functionality
        elif action == 'delete_car_type':
            car_type_id = request.POST.get('car_type_id')
            
            if car_type_id:
                try:
                    # Get car type using ORM
                    car_type = get_object_or_404(CarType, id=car_type_id)
                    car_type_name = car_type.name
                    
                    # Check if there are cars using this car type
                    cars_count = Car.objects.filter(car_type=car_type).count()
                    
                    if cars_count > 0:
                        messages.error(request, 'Cannot delete car type "{}". It is being used by {} car(s).'.format(
                            car_type_name, cars_count))
                        return redirect('custom_admin_car_types')
                    
                    # Check if there are bookings using this car type
                    bookings_count = Inquiry.objects.filter(car_type=car_type).count()
                    
                    if bookings_count > 0:
                        messages.error(request, 'Cannot delete car type "{}". It is referenced in {} booking(s).'.format(
                            car_type_name, bookings_count))
                        return redirect('custom_admin_car_types')
                    
                    # Delete the car type
                    car_type.delete()
                    
                    messages.success(request, 'Car type "{}" deleted successfully'.format(car_type_name))
                    logger.info("Car type deleted successfully: {} - ID {}".format(car_type_name, car_type_id))
                    return redirect('custom_admin_car_types')
                    
                except Exception as e:
                    messages.error(request, 'Error deleting car type: {}'.format(str(e)))
                    logger.error("Error deleting car type {}: {}".format(car_type_id, str(e)))
            else:
                messages.error(request, 'Car type ID is required for deletion.')
                
            return redirect('custom_admin_car_types')
        
        elif action == 'toggle_status':
            car_type_id = request.POST.get('car_type_id')
            new_status = request.POST.get('new_status')
            
            if car_type_id and new_status:
                try:
                    # Get car type using ORM
                    car_type = get_object_or_404(CarType, id=car_type_id)
                    
                    # Update status
                    car_type.is_active = new_status.lower() == 'true'
                    car_type.save(update_fields=['is_active'])
                    
                    status_text = 'activated' if car_type.is_active else 'deactivated'
                    messages.success(request, 'Car type "{}" {} successfully'.format(car_type.name, status_text))
                    logger.info("Car type {} {}: {}".format(car_type.name, status_text, car_type_id))
                    return redirect('custom_admin_car_types')
                    
                except Exception as e:
                    messages.error(request, 'Error updating car type status: {}'.format(str(e)))
                    logger.error("Error toggling status for car type {}: {}".format(car_type_id, str(e)))
            else:
                messages.error(request, 'Invalid request parameters.')
                
            return redirect('custom_admin_car_types')
    
    context = {
        'car_types': car_types,
    }
    
    return render(request, 'custom_admin/car_types.html', context)


@login_required
@user_passes_test(is_admin_user)
def custom_admin_routes(request):
    """Custom admin popular routes management - UPDATED FOR BLOB STORAGE"""
    routes = []
    
    try:
        # Use ORM instead of raw SQL
        routes = PopularRoute.objects.order_by('origin', 'destination')
        
        logger.info("Successfully loaded {} routes using ORM".format(routes.count()))
            
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
            route_image = request.FILES.get('route_image')
            
            if origin and destination and rate and distance:
                try:
                    # Validate numeric values
                    rate_decimal = Decimal(rate)
                    distance_decimal = Decimal(distance)
                    
                    if rate_decimal <= 0 or distance_decimal <= 0:
                        messages.error(request, 'Rate and distance must be positive numbers.')
                        return redirect('custom_admin_routes')
                    
                    # Create route using ORM
                    route = PopularRoute.objects.create(
                        origin=origin,
                        destination=destination,
                        rate=rate_decimal,
                        distance_km=distance_decimal,
                        is_active=True
                    )
                    
                    # ✅ UPDATED: Handle image upload to BLOB storage
                    if route_image:
                        route.set_image_from_file(route_image)
                        route.save()
                        logger.info("Image uploaded for new route {}".format(route.id))
                    
                    messages.success(request, 'Route {} → {} added successfully'.format(origin, destination))
                    logger.info('Route added successfully: {} → {}'.format(origin, destination))
                    
                except (ValueError, InvalidOperation):
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
            route_image = request.FILES.get('route_image')
            
            if route_id and origin and destination and rate and distance:
                try:
                    rate_decimal = Decimal(rate)
                    distance_decimal = Decimal(distance)
                    
                    if rate_decimal <= 0 or distance_decimal <= 0:
                        messages.error(request, 'Rate and distance must be positive numbers.')
                        return redirect('custom_admin_routes')
                    
                    # Get and update route using ORM
                    route = get_object_or_404(PopularRoute, id=route_id)
                    
                    # Update route using ORM
                    route.origin = origin
                    route.destination = destination
                    route.rate = rate_decimal
                    route.distance_km = distance_decimal
                    route.is_active = is_active
                    
                    # ✅ UPDATED: Handle image upload to BLOB storage
                    if route_image:
                        route.set_image_from_file(route_image)
                        logger.info("New image uploaded for route {}".format(route_id))
                    
                    route.save()
                    
                    messages.success(request, 'Route {} → {} updated successfully'.format(origin, destination))
                    logger.info("Route updated successfully: {} → {}".format(origin, destination))
                    return redirect('custom_admin_routes')
                    
                except (ValueError, InvalidOperation):
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
                    # Get and delete route using ORM
                    route = get_object_or_404(PopularRoute, id=route_id)
                    
                    # ✅ UPDATED: No need to delete files - images are stored in database
                    route.delete()
                    
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

class InquiryViewSet(viewsets.ModelViewSet):
    serializer_class = InquirySerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    
    def get_queryset(self):
        return Inquiry.objects.all().order_by('-created_at')
    
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
                            'distance': inquiry.safe_distance,  # Use safe property
                            'total_price': inquiry.safe_price,  # Use safe property
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
        """Get booking by booking ID - CONVERTED TO ORM"""
        booking_id = request.query_params.get('booking_id')
        
        if not booking_id:
            return Response({
                'success': False,
                'error': 'booking_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Use ORM instead of raw SQL
            booking = Inquiry.objects.select_related('car_type').filter(booking_id=booking_id).first()
            
            if booking:
                booking_data = {
                    'id': booking.id,
                    'booking_id': booking.booking_id,
                    'name': booking.name,
                    'email': booking.email,
                    'number': booking.number,
                    'origin': booking.origin,
                    'destination': booking.destination,
                    'datetime': booking.datetime.isoformat() if booking.datetime else None,
                    'return_datetime': booking.return_datetime.isoformat() if booking.return_datetime else None,
                    'trip_type': booking.trip_type,
                    'distance_km': booking.safe_distance,  # Use safe property
                    'price': booking.safe_price,  # Use safe property
                    'status': booking.status,
                    'special_requests': booking.special_requests,
                    'created_at': booking.created_at.isoformat() if booking.created_at else None,
                    'updated_at': booking.updated_at.isoformat() if booking.updated_at else None,
                    'car_type_name': booking.car_type.name if booking.car_type else None,
                }
                
                return Response({
                    'success': True,
                    'data': booking_data
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Booking not found'
                }, status=status.HTTP_404_NOT_FOUND)
                    
        except Exception as e:
            logger.error("Error fetching booking by ID: {}".format(str(e)))
            return Response({
                'success': False,
                'error': 'Database error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

def get_cars_data():
    """Get cars data consistently using ORM - UPDATED FOR BLOB STORAGE"""
    cars = []
    
    try:
        # Use ORM instead of raw SQL
        car_objects = Car.objects.select_related('car_type').order_by('car_type__name', 'name')
        
        for car in car_objects:
            try:
                # ✅ FIXED: Check if car has BLOB image data first, then fallback to file
                if car.image_data:
                    # Use database BLOB URL
                    image_url = f"/api/images/car/{car.id}/"
                elif car.image and hasattr(car.image, 'url'):
                    # Use file-based URL (legacy)
                    image_url = car.image.url
                else:
                    # No image available
                    image_url = ''
                
                car_data = {
                    'id': car.id,
                    'name': str(car.name) if car.name else 'Unknown Car',
                    'is_available': bool(car.is_available),
                    'car_type': {
                        'name': str(car.car_type.name) if car.car_type else 'Unknown',
                        'rate_per_km': safe_decimal_convert(car.car_type.rate_per_km) if car.car_type else 0
                    },
                    'image': image_url,    # ✅ FIXED: Use proper image URL
                    'has_image': bool(car.image_data) or bool(car.image)       # ✅ NEW: Boolean flag
                }
                cars.append(car_data)
            except Exception as car_error:
                logger.error("Error processing car {}: {}".format(car.id, str(car_error)))
                continue
                    
    except Exception as e:
        logger.error("Error loading cars: {}".format(str(e)))
        cars = []
    
    return cars

def our_cars(request):
    """Our Cars page view - displays all available cars from the database - ✅ UPDATED WITH DYNAMIC CAR TYPES"""
    cars = get_cars_data()
    
    # ✅ NEW: Get unique car types from cars that have actual vehicles
    car_types_with_cars = set()
    for car in cars:
        if car.get('car_type') and car['car_type'].get('name'):
            car_types_with_cars.add(car['car_type']['name'].lower())
    
    # ✅ NEW: Get all active car types from database for complete filter list
    try:
        all_car_types = CarType.objects.filter(is_active=True).order_by('name')
        available_car_types = []
        
        for car_type in all_car_types:
            car_type_data = {
                'name': car_type.name,
                'name_lower': car_type.name.lower(),
                'has_cars': car_type.name.lower() in car_types_with_cars
            }
            available_car_types.append(car_type_data)
            
    except Exception as e:
        logger.error("Error loading car types for filters: {}".format(str(e)))
        # Fallback to basic car types if database query fails
        available_car_types = [
            {'name': 'Hatchback', 'name_lower': 'hatchback', 'has_cars': 'hatchback' in car_types_with_cars},
            {'name': 'Sedan', 'name_lower': 'sedan', 'has_cars': 'sedan' in car_types_with_cars},
            {'name': 'SUV', 'name_lower': 'suv', 'has_cars': 'suv' in car_types_with_cars},
        ]
    
    context = {
        'cars': cars,
        'available_car_types': available_car_types,  # ✅ NEW: Pass car types for dynamic filters
        'page_title': 'Our Fleet',
        'page_description': 'Choose from our diverse range of well-maintained, luxury vehicles'
    }
    
    return render(request, 'our-cars.html', context)

@csrf_exempt
def car_availability_check(request):
    """API endpoint to check real-time car availability - CONVERTED TO ORM"""
    if request.method == 'GET':
        car_id = request.GET.get('car_id')
        
        if not car_id:
            return JsonResponse({'error': 'car_id parameter required'}, status=400)
        
        try:
            # Use ORM instead of raw SQL
            car = Car.objects.select_related('car_type').filter(id=car_id).first()
            
            if car:
                return JsonResponse({
                    'success': True,
                    'available': bool(car.is_available),
                    'car_name': str(car.name),
                    'car_type': str(car.car_type.name) if car.car_type else 'Unknown'
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
    """API endpoint for car-specific booking requests - CONVERTED TO ORM"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract car-specific data
            car_id = data.get('car_id')
            car_name = data.get('car_name', '')
            car_type = data.get('car_type', '').lower()
            
            # Validate car availability if specific car requested
            if car_id:
                car = Car.objects.filter(id=car_id).first()
                
                if not car:
                    return JsonResponse({
                        'success': False,
                        'error': 'Requested car not found'
                    }, status=404)
                
                if not car.is_available:  # Car not available
                    return JsonResponse({
                        'success': False,
                        'error': 'Car {} is currently not available'.format(car.name)
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
                        # Use ORM to assign car
                        inquiry.assigned_car_id = car_id
                        inquiry.save(update_fields=['assigned_car'])
                        logger.info("Car {} assigned to booking {}".format(car_name, inquiry.booking_id))
                    except Exception as assign_error:
                        logger.warning("Error assigning car with ID {} to booking: {}".format(car_id, str(assign_error)))
                
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

def home(request):
    """Home page view"""
    try:
        # Get popular routes for display
        popular_routes = PopularRoute.objects.filter(is_active=True)[:6]
        
        # Get available car types
        car_types = CarType.objects.filter(is_active=True)
        
        context = {
            'popular_routes': popular_routes,
            'car_types': car_types,
        }
        
        return render(request, 'booking/home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home view: {e}")
        messages.error(request, "An error occurred while loading the page.")
        return render(request, 'booking/home.html', {})


def booking_form(request):
    """Booking form page view"""
    try:
        car_types = CarType.objects.filter(is_active=True)
        popular_routes = PopularRoute.objects.filter(is_active=True)
        
        context = {
            'car_types': car_types,
            'popular_routes': popular_routes,
        }
        
        return render(request, 'booking/booking_form.html', context)
        
    except Exception as e:
        logger.error(f"Error in booking_form view: {e}")
        messages.error(request, "An error occurred while loading the booking form.")
        return render(request, 'booking/booking_form.html', {})


@csrf_exempt
@require_http_methods(["POST"])
def submit_booking(request):
    """Handle booking form submission"""
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Extract form data
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        number = data.get('number', '').strip()
        origin = data.get('origin', '').strip()
        destination = data.get('destination', '').strip()
        datetime_str = data.get('datetime', '').strip()
        return_datetime_str = data.get('return_datetime', '').strip()
        car_type_id = data.get('car_type_id')
        trip_type = data.get('trip_type', 'one-way')
        distance_km = data.get('distance_km', 0)
        price = data.get('price', 0)
        special_requests = data.get('special_requests', '').strip()
        
        # Validate required fields
        if not all([name, email, number, origin, destination, datetime_str, car_type_id]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields.'
            })
        
        # Get car type
        try:
            car_type = CarType.objects.get(id=car_type_id, is_active=True)
        except CarType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid car type selected.'
            })
        
        # Parse datetime
        try:
            from datetime import datetime
            pickup_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return_datetime = None
            if return_datetime_str:
                return_datetime = datetime.fromisoformat(return_datetime_str.replace('Z', '+00:00'))
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid date/time format.'
            })
        
        # Convert distance and price to Decimal
        try:
            distance_km = Decimal(str(distance_km))
            price = Decimal(str(price))
        except (InvalidOperation, ValueError):
            distance_km = Decimal('0.00')
            price = Decimal('0.00')
        
        # Create inquiry
        inquiry = Inquiry.objects.create(
            name=name,
            email=email,
            number=number,
            origin=origin,
            destination=destination,
            datetime=pickup_datetime,
            return_datetime=return_datetime,
            car_type=car_type,
            trip_type=trip_type,
            distance_km=distance_km,
            price=price,
            special_requests=special_requests,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Booking request submitted successfully!',
            'booking_id': inquiry.booking_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format.'
        })
    except Exception as e:
        logger.error(f"Error in submit_booking: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while processing your request.'
        })


def admin_dashboard(request):
    """Admin dashboard view"""
    try:
        # Get statistics
        total_bookings = Inquiry.objects.count()
        pending_bookings = Inquiry.objects.filter(status='pending').count()
        confirmed_bookings = Inquiry.objects.filter(status='confirmed').count()
        total_cars = Car.objects.count()
        available_cars = Car.objects.filter(is_available=True).count()
        total_routes = PopularRoute.objects.count()
        
        # Get recent bookings
        recent_bookings = Inquiry.objects.order_by('-created_at')[:5]
        
        context = {
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'confirmed_bookings': confirmed_bookings,
            'total_cars': total_cars,
            'available_cars': available_cars,
            'total_routes': total_routes,
            'recent_bookings': recent_bookings,
        }
        
        return render(request, 'booking/admin_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in admin_dashboard: {e}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return render(request, 'booking/admin_dashboard.html', {})


def admin_bookings(request):
    """Admin bookings management view"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        
        # Base queryset
        bookings = Inquiry.objects.all()
        
        # Apply filters
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        if search_query:
            bookings = bookings.filter(
                Q(booking_id__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(number__icontains=search_query) |
                Q(origin__icontains=search_query) |
                Q(destination__icontains=search_query)
            )
        
        # Order by creation date
        bookings = bookings.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(bookings, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'status_filter': status_filter,
            'search_query': search_query,
            'status_choices': Inquiry.STATUS_CHOICES,
        }
        
        return render(request, 'booking/admin_bookings.html', context)
        
    except Exception as e:
        logger.error(f"Error in admin_bookings: {e}")
        messages.error(request, "An error occurred while loading bookings.")
        return render(request, 'booking/admin_bookings.html', context)
