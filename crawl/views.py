import time

from django.db.models import Q
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Pub
from .models import Crawl
from .models import CrawlPub
from .geocoder import reverse_geocode
from .search import fetch_bars_nearby
from .tasks import create_pub_if_not_exists


MAX_RADIUS = 25000



def home(request):
    return HttpResponse("Welcome to the homepage!")


def crawl_detail(request, slug):
    crawl = get_object_or_404(Crawl, slug=slug)
    return render(request, "crawl/details.html", {
        "crawl": crawl,
        "pubs": [{**model_to_dict(stop.pub), **{'completed': stop.completed, 'position': stop.position}} for stop in CrawlPub.objects.filter(crawl=crawl).order_by('position')] 
    })


def fix_missing_addresses(request):
    pubs = Pub.objects.filter(Q(address_street_name__isnull=True) | Q(address_street_name=''))
    for pub in pubs:
        print(f'Fixing address for {pub}')
        location = reverse_geocode(pub.latitude, pub.longitude)
        # print(location['raw']['address'])
        pub.address_street_name = location['raw']['address'].get('road')
        pub.address_city = location['raw']['address'].get('city')
        pub.address_state = location['raw']['address'].get('state')
        pub.address_postcode = location['raw']['address'].get('postcode')
        pub.address_country_code = location['raw']['address'].get('country_code')
        pub.save()
        time.sleep(2.5)

    return JsonResponse({
        'data': {
            'addresses': len(pubs)
        }
    })


def import_pubs(request):
    longitude = float(request.GET.get("longitude"))
    latitude = float(request.GET.get("latitude"))
    radius = int(request.GET.get("radius", 5000))    # meters
    radius = min(radius, MAX_RADIUS)

    data = fetch_bars_nearby(lat=latitude, lon=longitude, radius=radius)
    pubs =  data['bars']
    for data in pubs:
        pub = create_pub_if_not_exists(data)

    return JsonResponse({
        'data': {
            'pubs': len(pubs)
        }
    })


