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


def search_pubs(request):
    # # 1. pull data and create inital dataframe
    # queryset = Pub.objects.all().values('id', 'name', 'longitude', 'latitude')
    queryset = Pub.objects.all().values()
    df = pd.DataFrame(list(queryset))
    df["longitude"] = df["longitude"].astype(float)
    df["latitude"] = df["latitude"].astype(float)
    df["created_at"] = df["created_at"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df["updated_at"] = df["updated_at"].dt.strftime("%Y-%m-%dT%H:%M:%S")

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
        return JsonResponse({
            'data': {
                'layer': json.loads(geojson_str)
            }
        })

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

    return JsonResponse({
        'data': {
            'layer': json.loads(geojson_str)
        }
    })

