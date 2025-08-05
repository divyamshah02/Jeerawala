from django.core.management.base import BaseCommand
from booking.models import PopularRoute
from decimal import Decimal

class Command(BaseCommand):
    help = 'Add dummy route data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing routes before adding new ones',
        )

    def handle(self, *args, **options):
        # Dummy route data
        dummy_routes = [
            {
                'origin': 'Mumbai',
                'destination': 'Pune',
                'distance_km': Decimal('148.5'),
                'rate': Decimal('2500.00'),
                'is_active': True
            },
            {
                'origin': 'Delhi',
                'destination': 'Agra',
                'distance_km': Decimal('233.0'),
                'rate': Decimal('3500.00'),
                'is_active': True
            },
            {
                'origin': 'Bangalore',
                'destination': 'Mysore',
                'distance_km': Decimal('144.0'),
                'rate': Decimal('2800.00'),
                'is_active': True
            },
            {
                'origin': 'Chennai',
                'destination': 'Pondicherry',
                'distance_km': Decimal('162.0'),
                'rate': Decimal('2200.00'),
                'is_active': True
            },
            {
                'origin': 'Ahmedabad',
                'destination': 'Udaipur',
                'distance_km': Decimal('262.0'),
                'rate': Decimal('4200.00'),
                'is_active': True
            },
            {
                'origin': 'Kolkata',
                'destination': 'Darjeeling',
                'distance_km': Decimal('610.0'),
                'rate': Decimal('8500.00'),
                'is_active': True
            },
            {
                'origin': 'Jaipur',
                'destination': 'Jodhpur',
                'distance_km': Decimal('337.0'),
                'rate': Decimal('5200.00'),
                'is_active': True
            },
            {
                'origin': 'Hyderabad',
                'destination': 'Vijayawada',
                'distance_km': Decimal('275.0'),
                'rate': Decimal('4000.00'),
                'is_active': True
            },
            {
                'origin': 'Kochi',
                'destination': 'Munnar',
                'distance_km': Decimal('130.0'),
                'rate': Decimal('3200.00'),
                'is_active': True
            },
            {
                'origin': 'Goa',
                'destination': 'Mumbai',
                'distance_km': Decimal('597.0'),
                'rate': Decimal('7800.00'),
                'is_active': True
            },
            {
                'origin': 'Chandigarh',
                'destination': 'Shimla',
                'distance_km': Decimal('117.0'),
                'rate': Decimal('2800.00'),
                'is_active': True
            },
            {
                'origin': 'Lucknow',
                'destination': 'Varanasi',
                'distance_km': Decimal('286.0'),
                'rate': Decimal('4500.00'),
                'is_active': True
            },
            {
                'origin': 'Surat',
                'destination': 'Mumbai',
                'distance_km': Decimal('284.0'),
                'rate': Decimal('4200.00'),
                'is_active': True
            },
            {
                'origin': 'Indore',
                'destination': 'Bhopal',
                'distance_km': Decimal('196.0'),
                'rate': Decimal('3200.00'),
                'is_active': True
            },
            {
                'origin': 'Coimbatore',
                'destination': 'Ooty',
                'distance_km': Decimal('89.0'),
                'rate': Decimal('2500.00'),
                'is_active': True
            }
        ]

        if options['clear']:
            PopularRoute.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Cleared all existing routes')
            )

        created_count = 0
        skipped_count = 0

        for route_data in dummy_routes:
            # Check if route already exists
            existing_route = PopularRoute.objects.filter(
                origin=route_data['origin'],
                destination=route_data['destination']
            ).first()
            
            if existing_route:
                self.stdout.write(
                    f"Route {route_data['origin']} → {route_data['destination']} already exists, skipping..."
                )
                skipped_count += 1
                continue
            
            try:
                route = PopularRoute.objects.create(**route_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created route: {route.origin} → {route.destination} (₹{route.rate})"
                    )
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error creating route {route_data['origin']} → {route_data['destination']}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n📊 Summary: Created {created_count} routes, Skipped {skipped_count} routes"
            )
        )
        self.stdout.write(
            f"Total routes in database: {PopularRoute.objects.count()}"
        )
