import logging

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Pub
from .models import Crawl
from .models import CrawlPub
from .search import fetch_bars_nearby
from .tasks import create_pub_if_not_exists


logger = logging.getLogger(__name__)


MAX_RADIUS = 25000


def home(request):
    return HttpResponse("Welcome to the homepage!")


def crawl_detail(request, slug):
    crawl = get_object_or_404(Crawl, slug=slug)
    return render(request, "crawl/details.html", {
        "crawl": crawl,
        "pubs": [{**model_to_dict(stop.pub), **{'completed': stop.completed, 'position': stop.position}} for stop in CrawlPub.objects.filter(crawl=crawl).order_by('position')] 
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


