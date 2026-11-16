import logging
from django.tasks import task

from .models import City
from .models import Pub
from .search import fetch_bars


def create_pub_if_not_exists(city, data):
    pub = Pub.objects.filter(external_id=data['id']).first()
    if not pub:
        logging.debug(f"Importing pub '{data['name']}'")
        pub = Pub.objects.create(
            name = data['name'],
            external_id = data['id'],
            subtype = data['type'],
            hours = data['hours'],
            website = data['website'],
            phone = data['phone'],
            address_street_number = data['housenumber'],
            address_street_name = data['street'],
            # street = data['address'],
            address_city = data['city'],
            address_postcode = data['postcode'],
            latitude = data['lat'],
            longitude = data['lon'],
            city = city
        )
        return pub
    return pub


@task
def process_new_city(city_id):
    city = City.objects.filter(pk=city_id).first()
    if city:
        logging.debug(f'Fetching pubs for {city}')
        for bar in fetch_bars(city.name)['bars']:
            pub = create_pub_if_not_exists(city, bar)

