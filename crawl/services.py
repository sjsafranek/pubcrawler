import pandas
import geopandas
from django.db.models import Q
from django.forms.models import model_to_dict

from .models import Pub
from .models import Crawl
from .models import CrawlPub
from .utils import getGeoJSONFromGeoDataFrame
from .geodata import downloadPubsWithinArea


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
    # area = geopandas.read_file(geom)
    area = geopandas.read_file(geom).to_crs("EPSG:4326")

    # Get bounding box from geometry
    minx, miny, maxx, maxy = area.total_bounds

    # Load pubs from within bounding box
    pubs = [
        model_to_dict(pub) for pub in Pub.objects.filter(Q(longitude__range=(minx, maxx)) & Q(latitude__range=(miny, maxy)))
    ]

    df = pandas.DataFrame(pubs)
    if 0 == len(df):
        return df
    bbox_gdf = makeGeoDataFrameFromDataFrame(df)

    # Filter pubs against geometry
    within_gdf = geopandas.sjoin(bbox_gdf, area, how="inner", predicate="within")
    return within_gdf


def getPubsByCrawlAsGeoDataFrame(crawl):
    pubs = getPubsByCrawlAsList(crawl)
    df = pandas.DataFrame(pubs)
    gdf = makeGeoDataFrameFromDataFrame(df)
    return gdf    


def createPubIfNotExists(data):
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
            latitude = data['latitude'],
            longitude = data['longitude']
        )
        return pub
    return pub


def importPubsWithinGeometry(geom):
    pubs = []
    records = downloadPubsWithinArea(geom)
    for record in records:
        pub = createPubIfNotExists(record)
        pubs.append(pub)
    return pubs

