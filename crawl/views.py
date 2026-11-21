import logging

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Pub
from .models import Crawl
from .models import CrawlPub
from .services import getPubsByCrawlAsList
from .services import getPubsByCrawlAsGeoDataFrame
from .services import getPubsWithinGeometryAsGeoDataFrame
from .services import importPubsWithinGeometry
from .utils import getGeoJSONFromGeoDataFrame

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

def buildNotFoundResponse():
    return buildErrorResponse('Not Found', 404)

def buildMethodNotAllowedResponse():
    return buildErrorResponse('Method Not Allowed', 405)

def buildMissingParameterResponse(parameter_name):
    return buildErrorResponse( f"Missing Parameter: '{parameter_name}'", 404)





def home(request):
    return HttpResponse("Welcome to the PubCrawler!")


def view_crawl_page(request, slug):
    crawl = get_object_or_404(Crawl, slug=slug)
    pubs = getPubsByCrawlAsList(crawl)
    return render(request, "crawl/details.html", {
        "crawl": crawl,
        "pubs": pubs
    })


def get_crawl_pubs(request, crawl_id):
    crawl = get_object_or_404(Crawl, id=crawl_id)
    gdf = getPubsByCrawlAsGeoDataFrame(crawl)
    geojson = getGeoJSONFromGeoDataFrame(gdf)
    api_response = buildSuccessResponse(layer=geojson)
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

    geom = request.GET.get("geom")
    pubs = importPubsWithinGeometry(geom)
    api_response = buildSuccessResponse(pubs=len(records))
    return JsonResponse(api_response)



def search_pubs(request):
    # Get geom from url parameters
    geom = request.GET.get("geom")
    query = request.GET.get("query")

    # Filter pubs against geometry
    pubs_gdf = getPubsWithinGeometryAsGeoDataFrame(geom)
    if 0 == len(pubs_gdf):
        api_response = buildNotFoundResponse()
        return JsonResponse(api_response)
    logger.debug(f"{len(pubs_gdf)} pubs found within '{geom}'")

    # If query is provided
    if query:
        logger.debug(query)
        pubs_gdf = pubs_gdf[pubs_gdf['name'].str.contains(query, case=False, na=False)]
        logger.debug(f"{len(pubs_gdf)} pubs found with query '%{query}%'")

    # Convert to GeoJson
    geojson = getGeoJSONFromGeoDataFrame(pubs_gdf)

    # Return response
    api_response = buildSuccessResponse(layer=geojson)
    return JsonResponse(api_response)

