from django.contrib import admin

from .models import City
from .models import Crawl
from .models import Pub
from .models import CrawlPub
from .forms import PubForm


admin.site.register(City)
admin.site.register(Crawl)
admin.site.register(CrawlPub)


@admin.register(Pub)
class PubAdmin(admin.ModelAdmin):
    form = PubForm
    change_form_template = "admin/geo_change_form.html"
