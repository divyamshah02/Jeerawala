from django.db import models
from django.core.validators import MinValueValidator, EmailValidator
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import logging
import base64

logger = logging.getLogger(__name__)

class CarType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    rate_per_km = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    # ✅ NEW: Add minimum and maximum rate fields for round-trip pricing
    minimum_rate_per_km = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Minimum rate per km for price range calculation")
    maximum_rate_per_km = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Maximum rate per km for price range calculation")
    minimum_distance_cap = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name) if self.name else "Unknown Car Type"
    
    def save(self, *args, **kwargs):
        # ✅ AUTO-SET: If min/max rates are not set, use the regular rate
        if not self.minimum_rate_per_km:
            self.minimum_rate_per_km = self.rate_per_km
        if not self.maximum_rate_per_km:
            self.maximum_rate_per_km = self.rate_per_km
        super().save(*args, **kwargs)


class Car(models.Model):
    car_type = models.ForeignKey(CarType, on_delete=models.CASCADE, related_name="cars")
    name = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    
    # OLD: File-based image storage (keep for backward compatibility during transition)
    image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    
    # NEW: Database BLOB storage
    image_data = models.BinaryField(blank=True, null=True, help_text='Binary image data')
    image_filename = models.CharField(max_length=255, blank=True, null=True, help_text='Original filename')
    image_content_type = models.CharField(max_length=100, blank=True, null=True, help_text='Image MIME type')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = str(self.name) if self.name else "Unknown Car"
        return name
    
    @property
    def has_image(self):
        """Check if car has an image (either file-based or BLOB)"""
        return bool(self.image_data) or bool(self.image)
    
    @property
    def image_url(self):
        """Get the URL for the car image"""
        if self.image_data:
            return f"/api/images/car/{self.id}/"
        elif self.image:
            return self.image.url
        return None
    
    def set_image_from_file(self, uploaded_file):
        """Store uploaded file as BLOB in database"""
        if uploaded_file:
            # Read file data
            uploaded_file.seek(0)  # Reset file pointer
            self.image_data = uploaded_file.read()
            self.image_filename = uploaded_file.name
            self.image_content_type = uploaded_file.content_type or 'image/jpeg'
            
            # Clear old file-based image
            if self.image:
                try:
                    self.image.delete(save=False)
                except:
                    pass
                self.image = None
    
    def get_image_data_url(self):
        """Get base64 data URL for inline display"""
        if self.image_data and self.image_content_type:
            encoded_data = base64.b64encode(self.image_data).decode('utf-8')
            return f"data:{self.image_content_type};base64,{encoded_data}"
        return None


class PopularRoute(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    # OLD: File-based image storage (keep for backward compatibility during transition)
    image = models.ImageField(upload_to='route_images/', blank=True, null=True)
    
    # NEW: Database BLOB storage
    image_data = models.BinaryField(blank=True, null=True, help_text='Binary image data')
    image_filename = models.CharField(max_length=255, blank=True, null=True, help_text='Original filename')
    image_content_type = models.CharField(max_length=100, blank=True, null=True, help_text='Image MIME type')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        origin = str(self.origin) if self.origin else "Unknown Origin"
        destination = str(self.destination) if self.destination else "Unknown Destination"
        return "{} → {}".format(origin, destination)
    
    @property
    def has_image(self):
        """Check if route has an image (either file-based or BLOB)"""
        return bool(self.image_data) or bool(self.image)
    
    @property
    def image_url(self):
        """Get the URL for the route image"""
        if self.image_data:
            return f"/api/images/route/{self.id}/"
        elif self.image:
            return self.image.url
        return None
    
    def set_image_from_file(self, uploaded_file):
        """Store uploaded file as BLOB in database"""
        if uploaded_file:
            # Read file data
            uploaded_file.seek(0)  # Reset file pointer
            self.image_data = uploaded_file.read()
            self.image_filename = uploaded_file.name
            self.image_content_type = uploaded_file.content_type or 'image/jpeg'
            
            # Clear old file-based image
            if self.image:
                try:
                    self.image.delete(save=False)
                except:
                    pass
                self.image = None
    
    def get_image_data_url(self):
        """Get base64 data URL for inline display"""
        if self.image_data and self.image_content_type:
            encoded_data = base64.b64encode(self.image_data).decode('utf-8')
            return f"data:{self.image_content_type};base64,{encoded_data}"
        return None


class Gallery(models.Model):
    title = models.CharField(max_length=200, help_text='Title for the gallery image')
    description = models.TextField(blank=True, null=True, help_text='Optional description for the image')
    
    # Image BLOB storage
    image_data = models.BinaryField(null=True, blank=True, help_text='Binary image data')
    image_filename = models.CharField(max_length=255, blank=True, null=True, help_text='Original filename')
    image_content_type = models.CharField(max_length=100, blank=True, null=True, help_text='Image MIME type')

    # Video BLOB storage
    video_data = models.BinaryField(blank=True, null=True, help_text='Binary video data')
    video_filename = models.CharField(max_length=255, blank=True, null=True, help_text='Original video filename')
    video_content_type = models.CharField(max_length=100, blank=True, null=True, help_text='Video MIME type')
    
    # Display order and status
    display_order = models.PositiveIntegerField(default=0, help_text='Order in which images appear (lower numbers first)')
    is_active = models.BooleanField(default=True, help_text='Whether this image is visible in the gallery')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    def __str__(self):
        return str(self.title) if self.title else f"Gallery Image {self.id}"
    
    @property
    def has_image(self):
        """Check if gallery item has an image"""
        return bool(self.image_data)
    
    @property
    def image_url(self):
        """Get the URL for the gallery image"""
        if self.image_data:
            return f"/api/images/gallery/{self.id}/"
        return None
    
    def set_image_from_file(self, uploaded_file):
        """Store uploaded file as BLOB in database"""
        if uploaded_file:
            # Remove old video
            self.video_data = None
            self.video_filename = None
            self.video_content_type = None
            
            # Save new image
            uploaded_file.seek(0)
            self.image_data = uploaded_file.read()
            self.image_filename = uploaded_file.name
            self.image_content_type = uploaded_file.content_type or 'image/jpeg'

    def set_video_from_file(self, uploaded_file):
        if uploaded_file:
            # Remove old image
            self.image_data = None
            self.image_filename = None
            self.image_content_type = None
            
            # Save new video
            uploaded_file.seek(0)
            self.video_data = uploaded_file.read()
            self.video_filename = uploaded_file.name
            self.video_content_type = uploaded_file.content_type or 'video/mp4'
    
    def get_image_data_url(self):
        """Get base64 data URL for inline display"""
        if self.image_data and self.image_content_type:
            encoded_data = base64.b64encode(self.image_data).decode('utf-8')
            return f"data:{self.image_content_type};base64,{encoded_data}"
        return None


# Keep existing Inquiry and other models unchanged
class InquiryManager(models.Manager):
    """Custom manager to handle decimal field issues safely"""
    
    def safe_get(self, **kwargs):
        """Get inquiry with safe decimal handling"""
        try:
            return self.get(**kwargs)
        except (InvalidOperation, ValueError) as e:
            logger.error(f"Decimal operation error in safe_get: {e}")
            return None
    
    def safe_filter(self, **kwargs):
        """Filter inquiries with safe decimal handling"""
        try:
            return self.filter(**kwargs)
        except (InvalidOperation, ValueError) as e:
            logger.error(f"Decimal operation error in safe_filter: {e}")
            return self.none()
    
    def get_safe_values(self, *fields):
        """Get values with safe decimal handling"""
        try:
            return self.values(*fields)
        except (InvalidOperation, ValueError) as e:
            logger.error(f"Decimal operation error in get_safe_values: {e}")
            return self.none().values(*fields)


class Inquiry(models.Model):
    TRIP_CHOICES = [
        ("one-way", "One Way"),
        ("round-trip", "Round Trip"),
        ("city", "City Roaming"),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic Information
    name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    number = models.CharField(max_length=15)
    
    # Trip Details
    origin = models.CharField(max_length=100, help_text="Pickup location")
    destination = models.CharField(max_length=100, help_text="Drop-off location")
    datetime = models.DateTimeField(help_text="Pickup date and time")
    return_datetime = models.DateTimeField(null=True, blank=True, help_text="Return date and time (for round trips)")
    
    # Car and Pricing
    car_type = models.ForeignKey(CarType, on_delete=models.SET_NULL, null=True)
    assigned_car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True)
    trip_type = models.CharField(max_length=20, choices=TRIP_CHOICES, default='one-way')
    distance_km = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Additional Information
    special_requests = models.TextField(blank=True, null=True)
    
    # Booking Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_id = models.CharField(max_length=20, unique=True, help_text="Unique booking identifier")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Admin fields
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin use")

    # Use custom manager
    objects = InquiryManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking Inquiry"
        verbose_name_plural = "Booking Inquiries"

    def __str__(self):
        booking_id = str(self.booking_id) if self.booking_id else "N/A"
        name = str(self.name) if self.name else "N/A"
        origin = str(self.origin) if self.origin else "N/A"
        destination = str(self.destination) if self.destination else "N/A"
        
        return "{} - {} ({} → {})".format(booking_id, name, origin, destination)
    
    def clean(self):
        """Clean method to ensure valid decimal values"""
        from django.core.exceptions import ValidationError
        
        # Ensure decimal fields have valid values
        try:
            if self.distance_km is None:
                self.distance_km = Decimal('0.00')
            elif isinstance(self.distance_km, str):
                self.distance_km = Decimal(self.distance_km)
        except (InvalidOperation, ValueError):
            self.distance_km = Decimal('0.00')
            
        try:
            if self.price is None:
                self.price = Decimal('0.00')
            elif isinstance(self.price, str):
                self.price = Decimal(self.price)
        except (InvalidOperation, ValueError):
            self.price = Decimal('0.00')
    
    def save(self, *args, **kwargs):
        # Clean before saving
        self.clean()
        
        if not self.booking_id:
            import random
            import string
            timestamp = str(int(timezone.now().timestamp()))
            random_suffix = ''.join(random.choices(string.digits, k=4))
            self.booking_id = "JTT{}{}".format(timestamp, random_suffix)
        
        super().save(*args, **kwargs)
    
    @property
    def safe_price(self):
        """Return price as float safely"""
        try:
            return float(self.price) if self.price else 0.0
        except (InvalidOperation, ValueError, TypeError):
            return 0.0
    
    @property
    def safe_distance(self):
        """Return distance as float safely"""
        try:
            return float(self.distance_km) if self.distance_km else 0.0
        except (InvalidOperation, ValueError, TypeError):
            return 0.0
    
    @property
    def is_round_trip(self):
        return self.trip_type == 'round-trip'
    
    @property
    def duration_days(self):
        if self.is_round_trip and self.return_datetime:
            return (self.return_datetime.date() - self.datetime.date()).days
        return 0
    
    @property
    def status_color(self):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'in_progress': '#17a2b8',
            'completed': '#6c757d',
            'cancelled': '#dc3545',
        }
        return colors.get(self.status, '#6c757d')


class BookingStatusHistory(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, choices=Inquiry.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Inquiry.STATUS_CHOICES)
    changed_by = models.CharField(max_length=100, default='System')
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = "Status History"
        verbose_name_plural = "Status Histories"
    
    def __str__(self):
        booking_id = str(self.inquiry.booking_id) if self.inquiry and self.inquiry.booking_id else "N/A"
        old_status = str(self.old_status) if self.old_status else "N/A"
        new_status = str(self.new_status) if self.new_status else "N/A"
        
        return "{}: {} → {}".format(booking_id, old_status, new_status)
