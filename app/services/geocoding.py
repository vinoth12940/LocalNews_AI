from typing import Dict, Optional
import pytz
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="local_news_app")
        self.cache = {}  # Simple in-memory cache

    def get_location_info(self, latitude: float, longitude: float) -> Dict:
        """
        Convert coordinates to location information including city, region, country, and timezone.
        """
        cache_key = f"{latitude},{longitude}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Get location information
            location = self.geolocator.reverse(f"{latitude}, {longitude}", language="en")
            if not location:
                raise ValueError("Could not find location information")

            # Extract address components
            address = location.raw.get('address', {})

            location_info = {
                "type": "approximate",
                "city": address.get('city') or address.get('town') or address.get('village'),
                "region": address.get('state') or address.get('county'),
                "country_code": address.get('country_code', '').upper(),
                "country": address.get('country'),
                "timezone": "UTC",  # Using UTC as default timezone
                "raw_address": location.address
            }

            # Cache the result
            self.cache[cache_key] = location_info
            return location_info

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            raise Exception(f"Geocoding service error: {str(e)}")

    def clear_cache(self):
        """Clear the geocoding cache."""
        self.cache.clear() 