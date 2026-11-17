from django.db import models
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
        return reverse("crawl_detail", kwargs={"slug": self.slug})        


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
                fields=["crawl", "position"],
                name="unique_pub_position_per_crawl"
            )
        ]

    def __str__(self):
        return f'{self.crawl}: {self.position} - {self.pub}'

