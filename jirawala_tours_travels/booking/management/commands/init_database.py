from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from booking.models import CarType

class Command(BaseCommand):
    help = 'Initialize database with required data'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Initializing database...")
        
        # Run migrations first
        self.stdout.write("📝 Running migrations...")
        try:
            call_command('migrate')
            self.stdout.write("✅ Migrations completed")
        except Exception as e:
            self.stdout.write(f"❌ Migration error: {e}")
            return
        
        # Create default car types
        self.stdout.write("🚗 Creating default car types...")
        car_types = [
            {'name': 'Hatchback', 'rate_per_km': 12.00},
            {'name': 'Sedan', 'rate_per_km': 15.00},
            {'name': 'SUV', 'rate_per_km': 18.00},
        ]
        
        for car_data in car_types:
            car_type, created = CarType.objects.get_or_create(
                name=car_data['name'],
                defaults={'rate_per_km': car_data['rate_per_km']}
            )
            if created:
                self.stdout.write(f"✅ Created car type: {car_type.name}")
            else:
                self.stdout.write(f"ℹ️ Car type already exists: {car_type.name}")
        
        # Test database connection
        self.stdout.write("🔍 Testing database connection...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM bookings_cartype")
                count = cursor.fetchone()[0]
                self.stdout.write(f"✅ Found {count} car types in database")
        except Exception as e:
            self.stdout.write(f"❌ Database test failed: {e}")
        
        self.stdout.write("🎉 Database initialization completed!")
