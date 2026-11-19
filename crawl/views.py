import json
import logging

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from .models import Pub
from .models import Crawl
from .models import CrawlPub
from .search import fetch_bars_nearby
from .tasks import create_pub_if_not_exists


logger = logging.getLogger(__name__)


MAX_RADIUS = 25000




def buildSuccessResponse(**kwargs):
    return {
        'status': 'ok',
        'data': {
            **kwargs
        }
    }

def buildErrorResponse(message, code=500):
    return {
        'status': 'error',
        'error': {
            'code': code,
            'message': message
        }
    }

def buildMethodNotAllowedResponse():
    return buildErrorResponse('Method Not Allowed', 405)

def buildMissingParameterResponse(parameter_name):
    return buildErrorResponse( f"Missing Parameter: '{parameter_name}'", 404)


def get_pubs_by_crawl(crawl):
    return [
        {
            **model_to_dict(stop.pub), 
            **{'completed': stop.completed, 'position': stop.position}
        } for stop in CrawlPub.objects.filter(crawl=crawl).order_by('position')
    ]


def makeGeoDataFrameFromDataFrame(df, longitude_column="longitude", latitude_column="latitude"):
    df["longitude"] = df["longitude"].astype(float)
    df["latitude"] = df["latitude"].astype(float)
    # Create the GeoDataFrame (match the SRID of your Django model, e.g., 4326)
    return gpd.GeoDataFrame(
            df, 
            geometry=gpd.points_from_xy(df[longitude_column], df[latitude_column]),
            crs="EPSG:4326"
        )


def home(request):
    return HttpResponse("Welcome to the PubCrawler!")


def view_crawl_page(request, slug):
    crawl = get_object_or_404(Crawl, slug=slug)
    return render(request, "crawl/details.html", {
        "crawl": crawl,
        "pubs": get_pubs_by_crawl(crawl)
    })


def get_crawl_pubs(request, crawl_id):
    crawl = get_object_or_404(Crawl, id=crawl_id)
    df = pd.DataFrame(get_pubs_by_crawl(crawl))
    gdf = makeGeoDataFrameFromDataFrame(df)
    geojson_str = gdf.to_json(to_wgs84=True, na="drop")
    api_response = buildSuccessResponse(layer=json.loads(geojson_str))
    return JsonResponse(api_response)


def toggle_crawl_pub(request, crawl_id, pub_id, action):
    if not request.user.is_authenticated:
        api_response = buildMethodNotAllowedResponse()
        return JsonResponse(api_response)

    # TODO :: Check user permissions
    
    crawl = get_object_or_404(Crawl, id=crawl_id)
    pub = get_object_or_404(Pub, id=pub_id)
    
    if 'add' == action:
        stop = CrawlPub(crawl=crawl, pub=pub, completed=False)        
        stop.save()
        api_response = buildSuccessResponse(pub={**model_to_dict(stop.pub), **{'completed': stop.completed, 'position': stop.position}})
        return JsonResponse(api_response)

    stop = CrawlPub.objects.get(crawl=crawl, pub=pub)
    if 'remove' == action:
        stop.delete()
        api_response = buildSuccessResponse()
        return JsonResponse(api_response) 
    elif 'complete' == action:
        stop.completed = True
        stop.save()
        api_response = buildSuccessResponse()
        return JsonResponse(api_response)
    elif 'incomplete' == action:
        stop.completed = False
        stop.save()
        api_response = buildSuccessResponse()
        return JsonResponse(api_response)         

    api_response = buildMethodNotAllowedResponse()
    return JsonResponse(api_response)


def import_pubs(request):
    if not request.user.is_authenticated:
        api_response = buildMethodNotAllowedResponse()
        return JsonResponse(api_response)

    # TODO :: Check user permissions
        
    longitude = float(request.GET.get("longitude"))
    latitude = float(request.GET.get("latitude"))
    radius = int(request.GET.get("radius", 5000))    # meters
    radius = min(radius, MAX_RADIUS)

    data = fetch_bars_nearby(lat=latitude, lon=longitude, radius=radius)
    pubs =  data['bars']
    for data in pubs:
        pub = create_pub_if_not_exists(data)

    api_response = buildSuccessResponse(pubs=len(pubs))
    return JsonResponse(api_response)


def search_pubs(request):
    # Get geom from url parameters
    geom = request.GET.get("geom")

    # Load GeoJson geometry
    area = gpd.read_file(geom)

    # Get bounding box from geometry
    minx, miny, maxx, maxy = area.total_bounds

    # Load pubs from within bounding box
    df = pd.DataFrame([
        model_to_dict(pub) for pub in Pub.objects.filter(longitude__range=(minx, maxx)).filter(latitude__range=(miny, maxy))
    ])
    gdf = makeGeoDataFrameFromDataFrame(df)

    logger.debug(f'{len(gdf)} pubs found within {minx}, {miny}, {maxx}, {maxy}')
    logger.debug(f'{len(gdf)} pubs found within {area.total_bounds}')

    # Filter pubs against geometry
    within_gdf = gpd.sjoin(gdf, area, how="inner", predicate="within")

    # logger.debug(f"{len(within_gdf)} pubs found within '{geom}'")

    # Convert to GeoJson
    geojson_str = within_gdf.to_json(to_wgs84=True, na="drop")

    # Return response
    api_response = buildSuccessResponse(layer=json.loads(geojson_str))
    return JsonResponse(api_response)

