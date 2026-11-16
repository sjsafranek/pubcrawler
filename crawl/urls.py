from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("crawl/<slug:slug>/", views.crawl_detail, name="crawl_detail"),
]
