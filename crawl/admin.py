from django.contrib import admin

# from .models import City
from .models import Crawl
from .models import Pub
from .models import CrawlPub
from .forms import PubForm


# admin.site.register(City)
admin.site.register(Crawl)
admin.site.register(CrawlPub)

@admin.register(Pub)
class PubAdmin(admin.ModelAdmin):
    form = PubForm
    change_list_template = "admin/pub_changelist.html"
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
                "run-bulk-job/",
                self.admin_site.admin_view(self.run_bulk_job),
                name="yourmodel-run-bulk-job",
            ),
        ]
        return custom_urls + urls

    def run_bulk_job(self, request):
        if request.method == "POST":
            # Trigger your bulk job or Celery task here
            # e.g., run_heavy_task.delay()
            self.message_user(request, "Bulk job started successfully.")
        return HttpResponseRedirect("../")