from geopy.geocoders import Nominatim


# Note: Nominatim requires a unique user_agent string to identify your application.
geolocator = Nominatim(user_agent="pubcrawler")


def forward_geocode(address_string):
    """Converts an address string into latitude and longitude coordinates."""
    location = geolocator.geocode(address_string, timeout=15)
    if location:
        return {
            "address": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "raw": location.raw
        }

def reverse_geocode(latitude, longitude):
    """Converts coordinate points back into a human-readable address."""
    location = geolocator.reverse((latitude, longitude), timeout=15)
    if location:
        return {
            "address": location.address,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "raw": location.raw
        }
