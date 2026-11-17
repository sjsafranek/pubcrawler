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




def home(request):
    return HttpResponse("Welcome to the homepage!")


def view_crawl_page(request, slug):
    crawl = get_object_or_404(Crawl, slug=slug)
    return render(request, "crawl/details.html", {
        "crawl": crawl,
        "pubs": [{**model_to_dict(stop.pub), **{'completed': stop.completed, 'position': stop.position}} for stop in CrawlPub.objects.filter(crawl=crawl).order_by('position')] 
    })


def get_crawl_pubs(request, crawl_id):
    crawl = get_object_or_404(Crawl, id=crawl_id)
    queryset = [
        {
            **model_to_dict(stop.pub), 
            **{'completed': stop.completed, 'position': stop.position}
        } for stop in CrawlPub.objects.filter(crawl=crawl).order_by('position')
    ]
    df = pd.DataFrame(queryset)
    df["longitude"] = df["longitude"].astype(float)
    df["latitude"] = df["latitude"].astype(float)
    gdf = gpd.GeoDataFrame(
            df, 
            geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
            crs="EPSG:4326"
        )
    geojson_str = gdf.to_json(to_wgs84=True, na="drop")
    api_response = buildSuccessResponse(layer=json.loads(geojson_str))
    return JsonResponse(api_response)


def toggle_crawl_pub(request, crawl_id, pub_id, yn):
    crawl = get_object_or_404(Crawl, id=crawl_id)
    pub = get_object_or_404(Pub, id=pub_id)
    stop = CrawlPub.objects.filter(crawl=crawl, pub=pub).first()
    stop.completed = yn;
    stop.save()
    api_response = buildSuccessResponse()
    return JsonResponse(api_response)


def import_pubs(request):
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
    # 1. pull data and create inital dataframe
    # pubs = Pub.objects.all().values()
    df = pd.DataFrame([model_to_dict(pub) for pub in Pub.objects.all()])
    df["longitude"] = df["longitude"].astype(float)
    df["latitude"] = df["latitude"].astype(float)

    # 2. Create the GeoDataFrame (match the SRID of your Django model, e.g., 4326)
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326"
    )

    # Use geom if supplied
    geom = request.GET.get("geom")
    if (geom):
        area = gpd.read_file(geom)
        within_gdf = gpd.sjoin(gdf, area, how="inner", predicate="within")
        geojson_str = within_gdf.to_json(to_wgs84=True, na="drop")
        api_response = buildSuccessResponse(layer=json.loads(geojson_str))
        return JsonResponse(api_response)

    # Get request attributes
    longitude = float(request.GET.get("longitude"))
    latitude = float(request.GET.get("latitude"))
    radius = int(request.GET.get("radius", 5000))    # meters
    radius = min(radius, MAX_RADIUS)
    
    # 2. Define your center point (lon, lat) and put it in a GeoSeries
    center = gpd.GeoSeries([Point(longitude, latitude)], crs="EPSG:4326")

    # 3. Project both to a metric CRS (e.g., Web Mercator EPSG:3857 or a local UTM zone)
    gdf_metric = gdf.to_crs(epsg=3857)
    center_metric = center.to_crs(epsg=3857)

    # 4. Filter by distance (e.g., within 5,000 meters)
    radius_meters = radius
    filtered_gdf = gdf[gdf_metric.distance(center_metric.iloc[0]) <= radius_meters]

    # Optional: Force re-projection to WGS84 (EPSG:4326) and drop missing values
    geojson_str = filtered_gdf.to_json(to_wgs84=True, na="drop")

    api_response = buildSuccessResponse(layer=json.loads(geojson_str))
    return JsonResponse(api_response)

