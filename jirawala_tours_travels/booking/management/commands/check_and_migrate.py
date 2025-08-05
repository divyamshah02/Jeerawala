from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.apps import apps

class Command(BaseCommand):
    help = 'Check database and run migrations if needed'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Checking database status...")
        
        # Check if tables exist
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'bookings_%';
            """)
            tables = cursor.fetchall()
            
        self.stdout.write(f"📊 Found {len(tables)} booking tables:")
        for table in tables:
            self.stdout.write(f"  - {table[0]}")
        
        # Check for pending migrations
        self.stdout.write("🔄 Checking for pending migrations...")
        try:
            call_command('showmigrations', '--plan')
        except Exception as e:
            self.stdout.write(f"❌ Migration check failed: {e}")
        
        # Make migrations
        self.stdout.write("📝 Creating new migrations...")
        try:
            call_command('makemigrations', 'bookings')
            self.stdout.write("✅ Migrations created successfully")
        except Exception as e:
            self.stdout.write(f"⚠️ Make migrations: {e}")
        
        # Run migrations
        self.stdout.write("🚀 Running migrations...")
        try:
            call_command('migrate')
            self.stdout.write("✅ Migrations completed successfully")
        except Exception as e:
            self.stdout.write(f"❌ Migration failed: {e}")
        
        # Check final table status
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'bookings_%';
            """)
            final_tables = cursor.fetchall()
            
        self.stdout.write(f"📊 Final table count: {len(final_tables)}")
        self.stdout.write("✅ Database check completed!")
