from rest_framework import serializers
from .models import Inquiry, CarType, Car, BookingStatusHistory
from decimal import Decimal, ROUND_HALF_UP
from .send_email import send_booking_email

class InquirySerializer(serializers.ModelSerializer):
    car_type_name = serializers.CharField(source='car_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    trip_type_display = serializers.CharField(source='get_trip_type_display', read_only=True)
    
    class Meta:
        model = Inquiry
        fields = [
            'id', 'name', 'email', 'number', 'origin', 'destination',
            'datetime', 'return_datetime', 'car_type', 'car_type_name', 'trip_type', 'trip_type_display',
            'distance_km', 'price', 'special_requests', 'status', 'status_display',
            'booking_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'booking_id']
    
    def validate_datetime(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Pickup date cannot be in the past.")
        return value
    
    def validate(self, data):
        if data.get('trip_type') == 'round-trip':
            if not data.get('return_datetime'):
                raise serializers.ValidationError("Return date is required for round trips.")
            if data.get('return_datetime') <= data.get('datetime'):
                raise serializers.ValidationError("Return date must be after pickup date.")
        return data


class BookingCreateSerializer(serializers.Serializer):
    """Serializer for frontend booking form data - CONVERTED TO ORM"""
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    tripType = serializers.CharField(max_length=20)
    pickupLocation = serializers.CharField(max_length=100)
    dropoffLocation = serializers.CharField(max_length=100)
    pickupDate = serializers.DateTimeField()
    dropoffDate = serializers.DateTimeField(required=False, allow_null=True)
    carType = serializers.CharField(max_length=20)
    totalPrice = serializers.DecimalField(max_digits=10, decimal_places=2)
    distance = serializers.DecimalField(max_digits=8, decimal_places=2)
    specialRequests = serializers.CharField(required=False, allow_blank=True)
    
    def validate_pickupDate(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Pickup date cannot be in the past.")
        return value
    
    def validate_totalPrice(self, value):
        """Custom validation for totalPrice to handle precision issues"""
        if value <= 0:
            raise serializers.ValidationError("Total price must be greater than 0.")
        # Round to 2 decimal places to avoid precision issues
        return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def validate_distance(self, value):
        """Custom validation for distance to handle precision issues"""
        if value <= 0:
            raise serializers.ValidationError("Distance must be greater than 0.")
        # Round to 2 decimal places to avoid precision issues
        return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def validate(self, data):
        if data.get('tripType') == 'round-trip':
            if not data.get('dropoffDate'):
                raise serializers.ValidationError("Drop-off date is required for round trips.")
            if data.get('dropoffDate') <= data.get('pickupDate'):
                raise serializers.ValidationError("Drop-off date must be after pickup date.")
        return data
    
    def create(self, validated_data):
        """Create inquiry using ORM - CONVERTED FROM RAW SQL"""
        import random
        import string
        from django.utils import timezone
        
        # Map frontend field names to model field names
        car_type_name = validated_data['carType'].lower()
        
        # Get or create car type using ORM
        car_type, created = CarType.objects.get_or_create(
            name__iexact=car_type_name,
            defaults={
                'name': car_type_name.capitalize(),
                'rate_per_km': 12 if car_type_name == 'hatchback' else 15 if car_type_name == 'sedan' else 18,
                'minimum_distance_cap': 0,
                'is_active': True
            }
        )
        
        # Generate booking ID
        timestamp = str(int(timezone.now().timestamp()))
        random_suffix = ''.join(random.choices(string.digits, k=4))
        booking_id = "JTT{}{}".format(timestamp, random_suffix)
        
        # Create inquiry using ORM
        inquiry = Inquiry.objects.create(
            name=validated_data['name'],
            email=validated_data['email'],
            number=validated_data['phone'],
            origin=validated_data['pickupLocation'],
            destination=validated_data['dropoffLocation'],
            datetime=validated_data['pickupDate'],
            return_datetime=validated_data.get('dropoffDate'),
            car_type=car_type,
            trip_type=validated_data['tripType'],
            distance_km=validated_data['distance'],
            price=validated_data['totalPrice'],
            special_requests=validated_data.get('specialRequests', ''),
            status='pending',
            booking_id=booking_id,
            is_active=True
        )
        
        send_booking_email(
                gmail_user="jirawalataxi@gmail.com",
                gmail_password="wmwc owcv fhbu rcgk",  # use App Password, not Gmail password
                name=validated_data['name'],
                email=validated_data['email'],
                number=validated_data['phone'],
                origin=validated_data['pickupLocation'],
                destination=validated_data['dropoffLocation'],
                datetime_=validated_data['pickupDate'],
                return_datetime=validated_data.get('dropoffDate'),
                car_type=car_type,
                trip_type=validated_data['tripType'],
            )

        # Create initial status history using ORM
        BookingStatusHistory.objects.create(
            inquiry=inquiry,
            old_status='',
            new_status='pending',
            changed_by='Customer',
            notes='Booking created by customer'
        )
        
        return inquiry


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = [
            'id',
            'name',
            'registration_number',
            'is_available',
            'driver_name',
            'driver_contact',
            'car_type_id',
        ]
