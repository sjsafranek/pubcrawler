from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path

from .models import Crawl
from .models import Pub
from .models import CrawlPub
from .forms import PubForm
from .tasks import fix_missing_addresses


admin.site.register(Crawl)
admin.site.register(CrawlPub)

@admin.register(Pub)
class PubAdmin(admin.ModelAdmin):
    form = PubForm
    change_list_template = "admin/pub_change_list.html"
    change_form_template = "admin/geo_change_form.html"
    list_display = [
        "name",
        "subtype",
        "address_street_number",
        "address_street_name",
        "address_city",
        "address_postcode"
    ]
    search_fields = ["name", "address_city", "address_postcode"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "fix-missing-addresses/",
                self.admin_site.admin_view(self.fix_missing_addresses),
                name="pub-fix-missing-addresses",
            ),
        ]
        return custom_urls + urls

    def fix_missing_addresses(self, request):
        if request.method == "POST":
            fix_missing_addresses()
            self.message_user(request, "Fix Addresses started successfully.")
        return HttpResponseRedirect("../")

