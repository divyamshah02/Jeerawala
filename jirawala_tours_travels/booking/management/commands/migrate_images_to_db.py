from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from booking.models import Car, PopularRoute
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate existing file-based images to database BLOB storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if BLOB data already exists',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Starting image migration to database...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Migrate car images
        self.migrate_car_images(dry_run, force)
        
        # Migrate route images
        self.migrate_route_images(dry_run, force)
        
        self.stdout.write(self.style.SUCCESS('Image migration completed!'))

    def migrate_car_images(self, dry_run=False, force=False):
        """Migrate car images from files to BLOB"""
        self.stdout.write('\n--- Migrating Car Images ---')
        
        cars_with_files = Car.objects.exclude(image='')
        total_cars = cars_with_files.count()
        
        if total_cars == 0:
            self.stdout.write('No cars with file-based images found.')
            return
        
        self.stdout.write(f'Found {total_cars} cars with file-based images')
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for car in cars_with_files:
            try:
                # Skip if already has BLOB data and not forcing
                if car.image_data and not force:
                    self.stdout.write(f'  SKIP: {car.name} - Already has BLOB data')
                    skipped += 1
                    continue
                
                # Check if file exists
                if not default_storage.exists(car.image.name):
                    self.stdout.write(
                        self.style.WARNING(f'  MISSING: {car.name} - File not found: {car.image.name}')
                    )
                    errors += 1
                    continue
                
                if dry_run:
                    self.stdout.write(f'  WOULD MIGRATE: {car.name} - {car.image.name}')
                    migrated += 1
                    continue
                
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
                
                self.stdout.write(
                    self.style.SUCCESS(f'  MIGRATED: {car.name} - {filename} ({len(image_data)} bytes)')
                )
                migrated += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ERROR: {car.name} - {str(e)}')
                )
                errors += 1
        
        self.stdout.write(f'\nCar Images Summary:')
        self.stdout.write(f'  Migrated: {migrated}')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Errors: {errors}')

    def migrate_route_images(self, dry_run=False, force=False):
        """Migrate route images from files to BLOB"""
        self.stdout.write('\n--- Migrating Route Images ---')
        
        routes_with_files = PopularRoute.objects.exclude(image='')
        total_routes = routes_with_files.count()
        
        if total_routes == 0:
            self.stdout.write('No routes with file-based images found.')
            return
        
        self.stdout.write(f'Found {total_routes} routes with file-based images')
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for route in routes_with_files:
            try:
                # Skip if already has BLOB data and not forcing
                if route.image_data and not force:
                    self.stdout.write(f'  SKIP: {route.origin} → {route.destination} - Already has BLOB data')
                    skipped += 1
                    continue
                
                # Check if file exists
                if not default_storage.exists(route.image.name):
                    self.stdout.write(
                        self.style.WARNING(f'  MISSING: {route.origin} → {route.destination} - File not found: {route.image.name}')
                    )
                    errors += 1
                    continue
                
                if dry_run:
                    self.stdout.write(f'  WOULD MIGRATE: {route.origin} → {route.destination} - {route.image.name}')
                    migrated += 1
                    continue
                
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
                
                self.stdout.write(
                    self.style.SUCCESS(f'  MIGRATED: {route.origin} → {route.destination} - {filename} ({len(image_data)} bytes)')
                )
                migrated += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ERROR: {route.origin} → {route.destination} - {str(e)}')
                )
                errors += 1
        
        self.stdout.write(f'\nRoute Images Summary:')
        self.stdout.write(f'  Migrated: {migrated}')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Errors: {errors}')
