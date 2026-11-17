from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("crawl/<slug:slug>/", views.crawl_detail, name="crawl_detail"),
    path("api/v1/pubs/import", views.import_pubs, name="import_pubs"),
    path("api/v1/pubs/search", views.search_pubs, name="search_pubs")
]

