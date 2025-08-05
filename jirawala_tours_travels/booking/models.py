from django.db import models
from django.core.validators import MinValueValidator, EmailValidator
from django.utils import timezone

class CarType(models.Model):
    name = models.CharField(max_length=50, choices=[("SUV", "SUV"), ("Sedan", "Sedan"), ("Hatchback", "Hatchback")])
    rate_per_km = models.DecimalField(max_digits=6, decimal_places=2)
    minimum_distance_cap = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name) if self.name else "Unknown Car Type"


class Car(models.Model):
    car_type = models.ForeignKey(CarType, on_delete=models.CASCADE, related_name="cars")
    name = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=20, unique=True)
    is_available = models.BooleanField(default=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_contact = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = str(self.name) if self.name else "Unknown Car"
        registration = str(self.registration_number) if self.registration_number else "No Registration"
        return "{} ({})".format(name, registration)


class PopularRoute(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    rate = models.CharField(max_length=100)
    distance_km = models.CharField(max_length=100)
    image = models.ImageField(upload_to='route_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        origin = str(self.origin) if self.origin else "Unknown Origin"
        destination = str(self.destination) if self.destination else "Unknown Destination"
        return "{} → {}".format(origin, destination)


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
    distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    
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
    
    def save(self, *args, **kwargs):
        if not self.booking_id:
            import random
            import string
            timestamp = str(int(timezone.now().timestamp()))
            random_suffix = ''.join(random.choices(string.digits, k=4))
            self.booking_id = "JTT{}{}".format(timestamp, random_suffix)
        super().save(*args, **kwargs)
    
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
