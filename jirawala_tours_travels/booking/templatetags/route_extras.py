from django import template
from django.templatetags.static import static

register = template.Library()

@register.filter
def get_route_image(route):
    """Get the appropriate image for a route based on cities"""
    
    # If route has a custom image, use it
    if hasattr(route, 'route_image') and route.route_image:
        return route.route_image.url
    
    # City to image mapping
    city_images = {
        'mumbai': 'img/cities/mumbai.jpg',
        'pune': 'img/cities/pune.jpg',
        'delhi': 'img/cities/delhi.jpg',
        'agra': 'img/cities/agra.jpg',
        'bangalore': 'img/cities/bangalore.jpg',
        'bengaluru': 'img/cities/bangalore.jpg',  # Alternative name
        'mysore': 'img/cities/mysore.jpg',
        'chennai': 'img/cities/chennai.jpg',
        'pondicherry': 'img/cities/pondicherry.jpg',
        'puducherry': 'img/cities/pondicherry.jpg',  # Alternative name
        'ahmedabad': 'img/cities/ahmedabad.jpg',
        'vadodara': 'img/cities/vadodara.jpg',
        'surat': 'img/cities/surat.jpg',
        'rajkot': 'img/cities/rajkot.jpg',
        'udaipur': 'img/cities/udaipur.jpg',
        'kolkata': 'img/cities/kolkata.jpg',
        'darjeeling': 'img/cities/darjeeling.jpg',
        'jaipur': 'img/cities/jaipur.jpg',
        'jodhpur': 'img/cities/jodhpur.jpg',
        'hyderabad': 'img/cities/hyderabad.jpg',
        'vijayawada': 'img/cities/vijayawada.jpg',
        'kochi': 'img/cities/kochi.jpg',
        'cochin': 'img/cities/kochi.jpg',  # Alternative name
        'munnar': 'img/cities/munnar.jpg',
        'goa': 'img/cities/goa.jpg',
        'panaji': 'img/cities/goa.jpg',  # Goa capital
        'chandigarh': 'img/cities/chandigarh.jpg',
        'shimla': 'img/cities/shimla.jpg',
        'lucknow': 'img/cities/lucknow.jpg',
        'varanasi': 'img/cities/varanasi.jpg',
        'banaras': 'img/cities/varanasi.jpg',  # Alternative name
        'indore': 'img/cities/indore.jpg',
        'bhopal': 'img/cities/bhopal.jpg',
        'coimbatore': 'img/cities/coimbatore.jpg',
        'ooty': 'img/cities/ooty.jpg',
        'ootacamund': 'img/cities/ooty.jpg',  # Full name
        'nashik': 'img/cities/nashik.jpg',
        'aurangabad': 'img/cities/aurangabad.jpg',
        'nagpur': 'img/cities/nagpur.jpg',
        'solapur': 'img/cities/solapur.jpg',
        'amritsar': 'img/cities/amritsar.jpg',
        'ludhiana': 'img/cities/ludhiana.jpg',
        'dehradun': 'img/cities/dehradun.jpg',
        'haridwar': 'img/cities/haridwar.jpg',
        'rishikesh': 'img/cities/rishikesh.jpg',
        'manali': 'img/cities/manali.jpg',
        'dharamshala': 'img/cities/dharamshala.jpg',
        'mcleodganj': 'img/cities/dharamshala.jpg',
        'mount abu': 'img/cities/mount-abu.jpg',
        'pushkar': 'img/cities/pushkar.jpg',
        'bikaner': 'img/cities/bikaner.jpg',
        'ajmer': 'img/cities/ajmer.jpg',
    }
    
    # Get origin and destination in lowercase
    if hasattr(route, 'destination'):
        destination = route.destination.lower().strip()
    else:
        destination = route.get('destination', '').lower().strip()
        
    if hasattr(route, 'origin'):
        origin = route.origin.lower().strip()
    else:
        origin = route.get('origin', '').lower().strip()
    
    # Try destination first (usually more scenic), then origin
    if destination in city_images:
        return static(city_images[destination])
    elif origin in city_images:
        return static(city_images[origin])
    else:
        # Return a default scenic route image
        return static('img/cities/default-route.jpg')

@register.filter
def get_route_alt_text(route):
    """Generate appropriate alt text for route images"""
    if hasattr(route, 'destination') and hasattr(route, 'origin'):
        return f"Scenic view of {route.destination} - {route.origin} to {route.destination} route"
    else:
        destination = route.get('destination', 'destination')
        origin = route.get('origin', 'origin')
        return f"Scenic view of {destination} - {origin} to {destination} route"

@register.filter
def get_car_image(route):
    """Get appropriate car image based on route distance"""
    if hasattr(route, 'distance_km'):
        distance = float(route.distance_km) if route.distance_km else 0
    else:
        distance = float(route.get('distance_km', 0))
    
    # Use different car types based on distance
    if distance > 500:  # Long distance routes
        return static('img/car-suv.png')
    elif distance > 200:  # Medium distance routes
        return static('img/car-sedan.png')
    else:  # Short distance routes
        return static('img/car-hatchback.png')
