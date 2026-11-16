from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Crawl
from .models import CrawlPub


def home(request):
    return HttpResponse("Welcome to the homepage!")


def crawl_detail(request, slug):
    crawl = get_object_or_404(Crawl, slug=slug)
    return render(request, "crawl/details.html", {
        "crawl": crawl,
        "pubs": [stop.pub for stop in CrawlPub.objects.filter(crawl=crawl).order_by('position')] 
    })
    # return JsonResponse({
    #     'data': {
    #         'name': crawl.name, 
    #         'pubs': [
    #             stop.pub.name for stop in CrawlPub.objects.filter(crawl=crawl)
    #         ] 
    #     }
    # })

