from django.urls import path
from django.urls import re_path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("crawl/<slug:slug>", views.view_crawl_page, name="view_crawl_page"),
    path("api/v1/crawl/<int:crawl_id>/pubs", views.get_crawl_pubs, name="get_crawl_pubs"),
    path("api/v1/crawl/<int:crawl_id>/pub/<int:pub_id>/<str:action>", views.toggle_crawl_pub, name="toggle_crawl_pub"),
    path("api/v1/pubs/import", views.import_pubs, name="import_pubs"),
    path("api/v1/pubs/search", views.search_pubs, name="search_pubs")
]

