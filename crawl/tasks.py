import time
import logging
from django.db.models import Q
from django.tasks import task

from .models import Pub
from .search import fetch_bars
from .geocoder import reverse_geocode


logger = logging.getLogger(__name__)


def create_pub_if_not_exists(data):
    pub = Pub.objects.filter(external_id=data['id']).first()
    if not pub:
        logger.debug(f"Importing pub '{data['name']}'")
        pub = Pub.objects.create(
            name = data['name'],
            external_id = data['id'],
            subtype = data['type'],
            hours = data['hours'],
            website = data['website'],
            phone = data['phone'],
            address_street_number = data['housenumber'],
            address_street_name = data['street'],
            address_city = data['city'],
            address_postcode = data['postcode'],
            latitude = data['lat'],
            longitude = data['lon']
        )
        return pub
    return pub


# @task
# def process_new_city(city_id):
#     city = City.objects.filter(pk=city_id).first()
#     if city:
#         logger.debug(f'Fetching pubs for {city}')
#         for bar in fetch_bars(city.name)['bars']:
#             pub = create_pub_if_not_exists(bar)


def fix_missing_addresses():
    pubs = Pub.objects.filter(Q(address_street_name__isnull=True) | Q(address_street_name=''))
    for pub in pubs:
        logger.debug(f'Fixing address for {pub}')
        location = reverse_geocode(pub.latitude, pub.longitude)
        # print(location['raw']['address'])
        pub.address_street_number = locatino['raw']['address'].get('house_number')
        pub.address_street_name = location['raw']['address'].get('road')
        pub.address_city = location['raw']['address'].get('city')
        pub.address_state = location['raw']['address'].get('state')
        pub.address_postcode = location['raw']['address'].get('postcode')
        pub.address_country_code = location['raw']['address'].get('country_code')
        pub.save()
        time.sleep(2.5)
