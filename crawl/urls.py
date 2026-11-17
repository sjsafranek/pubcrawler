from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("crawl/<slug:slug>/", views.crawl_detail, name="crawl_detail"),
    path("api/v1/pubs/fix_missing_addresses", views.fix_missing_addresses, name="fix_missing_addresses"),
    path("api/v1/pubs/import", views.import_pubs, name="import_pubs"),
]

