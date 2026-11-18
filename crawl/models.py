from django.db import models
from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class Crawl(TimeStampedModel):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("view_crawl_page", kwargs={"slug": self.slug})        


class Pub(TimeStampedModel):
    name = models.CharField(max_length=256)
    external_id = models.CharField(max_length=256, unique=True, null=True, blank=True)
    subtype = models.CharField(max_length=56)
    hours = models.CharField(max_length=126, null=True, blank=True)
    website = models.CharField(max_length=256, null=True, blank=True)
    phone = models.CharField(max_length=126, null=True, blank=True)
    address_street_number = models.CharField(max_length=126, null=True, blank=True)
    address_street_name = models.CharField(max_length=126, null=True, blank=True)
    address_city = models.CharField(max_length=126, null=True, blank=True)
    address_state = models.CharField(max_length=126, null=True, blank=True)
    address_postcode = models.CharField(max_length=126, null=True, blank=True)
    address_country_code = models.CharField(max_length=8, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f'{self.name} ({self.address_city})'


class CrawlPub(models.Model):
    crawl = models.ForeignKey(Crawl, on_delete=models.CASCADE)
    pub = models.ForeignKey(Pub, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["crawl", "pub"],
                name="unique_pub_per_crawl"
            ),
            models.UniqueConstraint(
                fields=["crawl", "position"],
                name="unique_position_per_crawl"
            )
        ]

    def save(self, *args, **kwargs):
        if self._state.adding and not self.order:
            max_position = CrawlPub.objects.aggregate(Max("position"))["position__max"]
            self.position = (max_position or 0) + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            crawl = self.crawl
            deleted_position = self.position
            super().delete(*args, **kwargs)
            # Decrement order for all rows that came after the deleted row
            CrawlPub.objects.filter(order__gt=deleted_position, crawl=crawl).update(
                order=F('position') - 1
            )

    def __str__(self):
        return f'{self.crawl}: {self.position} - {self.pub}'

