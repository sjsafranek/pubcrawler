from django.db import models
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class City(TimeStampedModel):
    name = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return self.name


class Crawl(TimeStampedModel):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    city = models.ForeignKey(
        City, 
        on_delete=models.DO_NOTHING,
        related_name='crawls',
        null=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("crawl_detail", kwargs={"slug": self.slug})        


class Pub(TimeStampedModel):
    name = models.CharField(max_length=256)
    city = models.ForeignKey(
        City, 
        on_delete=models.CASCADE,
        related_name='pubs'
    )
    external_id = models.CharField(max_length=256, unique=True, null=True, blank=True)
    subtype = models.CharField(max_length=56)
    hours = models.CharField(max_length=126, null=True, blank=True)
    website = models.CharField(max_length=256, null=True, blank=True)
    phone = models.CharField(max_length=126, null=True, blank=True)
    address_street_number = models.CharField(max_length=126, null=True, blank=True)
    address_street_name = models.CharField(max_length=126, null=True, blank=True)
    address_city = models.CharField(max_length=126, null=True, blank=True)
    address_postcode = models.CharField(max_length=126, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f'{self.name} ({self.city})'

    @property
    def geomap_longitude(self):
        return '' if self.longitude is None else str(self.longitude)

    @property
    def geomap_latitude(self):
        return '' if self.latitude is None else str(self.latitude)


class CrawlPub(models.Model):
    crawl = models.ForeignKey(Crawl, on_delete=models.CASCADE)
    pub = models.ForeignKey(Pub, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["crawl", "position"],
                name="unique_pub_position_per_crawl"
            )
        ]

    def __str__(self):
        return f'{self.crawl}: {self.position} - {self.pub}'

