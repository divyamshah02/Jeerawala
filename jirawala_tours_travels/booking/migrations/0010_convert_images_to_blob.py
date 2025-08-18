# Data migration to convert existing file-based images to BLOB storage
from django.db import migrations
from django.core.files.storage import default_storage
import os
import logging

logger = logging.getLogger(__name__)

def convert_car_images_to_blob(apps, schema_editor):
    """Convert existing car images from files to BLOB"""
    Car = apps.get_model('booking', 'Car')
    
    for car in Car.objects.all():
        if car.image and hasattr(car.image, 'path'):
            try:
                # Check if file exists
                if default_storage.exists(car.image.name):
                    # Read the image file
                    with default_storage.open(car.image.name, 'rb') as image_file:
                        image_data = image_file.read()
                    
                    # Get filename and content type
                    filename = os.path.basename(car.image.name)
                    content_type = 'image/jpeg'  # Default
                    
                    if filename.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif filename.lower().endswith('.gif'):
                        content_type = 'image/gif'
                    elif filename.lower().endswith('.webp'):
                        content_type = 'image/webp'
                    
                    # Store in BLOB fields
                    car.image_data = image_data
                    car.image_filename = filename
                    car.image_content_type = content_type
                    car.save(update_fields=['image_data', 'image_filename', 'image_content_type'])
                    
                    logger.info(f"Converted car image: {car.name} - {filename}")
                else:
                    logger.warning(f"Image file not found for car {car.name}: {car.image.name}")
                    
            except Exception as e:
                logger.error(f"Error converting car image for {car.name}: {str(e)}")

def convert_route_images_to_blob(apps, schema_editor):
    """Convert existing route images from files to BLOB"""
    PopularRoute = apps.get_model('booking', 'PopularRoute')
    
    for route in PopularRoute.objects.all():
        if route.image and hasattr(route.image, 'path'):
            try:
                # Check if file exists
                if default_storage.exists(route.image.name):
                    # Read the image file
                    with default_storage.open(route.image.name, 'rb') as image_file:
                        image_data = image_file.read()
                    
                    # Get filename and content type
                    filename = os.path.basename(route.image.name)
                    content_type = 'image/jpeg'  # Default
                    
                    if filename.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif filename.lower().endswith('.gif'):
                        content_type = 'image/gif'
                    elif filename.lower().endswith('.webp'):
                        content_type = 'image/webp'
                    
                    # Store in BLOB fields
                    route.image_data = image_data
                    route.image_filename = filename
                    route.image_content_type = content_type
                    route.save(update_fields=['image_data', 'image_filename', 'image_content_type'])
                    
                    logger.info(f"Converted route image: {route.origin} → {route.destination} - {filename}")
                else:
                    logger.warning(f"Image file not found for route {route.origin} → {route.destination}: {route.image.name}")
                    
            except Exception as e:
                logger.error(f"Error converting route image for {route.origin} → {route.destination}: {str(e)}")

def reverse_conversion(apps, schema_editor):
    """Reverse migration - clear BLOB data"""
    Car = apps.get_model('booking', 'Car')
    PopularRoute = apps.get_model('booking', 'PopularRoute')
    
    Car.objects.update(image_data=None, image_filename=None, image_content_type=None)
    PopularRoute.objects.update(image_data=None, image_filename=None, image_content_type=None)

class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0009_add_image_blob_fields'),
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: (
                convert_car_images_to_blob(apps, schema_editor),
                convert_route_images_to_blob(apps, schema_editor)
            ),
            reverse_code=reverse_conversion,
        ),
    ]
