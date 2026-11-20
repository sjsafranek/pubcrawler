import pandas
import geopandas
from django.db.models import Q
from django.forms.models import model_to_dict

from .models import Pub
from .models import Crawl
from .models import CrawlPub
from .utils import getGeoJSONFromGeoDataFrame



def makeGeoDataFrameFromDataFrame(df, longitude_column="longitude", latitude_column="latitude"):
    df["longitude"] = df["longitude"].astype(float)
    df["latitude"] = df["latitude"].astype(float)
    return geopandas.GeoDataFrame(
                    df, 
                    geometry=geopandas.points_from_xy(df[longitude_column], df[latitude_column]),
                    crs="EPSG:4326"
                )


def getPubsByCrawlAsList(crawl):
    return [
        {
            **model_to_dict(stop.pub), 
            **{'completed': stop.completed, 'position': stop.position}
        } for stop in CrawlPub.objects.filter(crawl=crawl).order_by('position')
    ]


def getPubsWithinGeometryAsGeoDataFrame(geom):
    # Load GeoJson geometry
    area = geopandas.read_file(geom)

    # Get bounding box from geometry
    minx, miny, maxx, maxy = area.total_bounds

    # Load pubs from within bounding box
    df = pandas.DataFrame([
        model_to_dict(pub) for pub in Pub.objects.filter(Q(longitude__range=(minx, maxx)) & Q(latitude__range=(miny, maxy)))
    ])
    bbox_gdf = makeGeoDataFrameFromDataFrame(df)

    # Filter pubs against geometry
    within_gdf = geopandas.sjoin(bbox_gdf, area, how="inner", predicate="within")
    return within_gdf


def getPubsByCrawlAsGeoDataFrame(crawl):
    pubs = getPubsByCrawlAsList(crawl)
    df = pandas.DataFrame(pubs)
    gdf = makeGeoDataFrameFromDataFrame(df)
    return gdf    

