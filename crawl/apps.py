from django.apps import AppConfig


class CrawlConfig(AppConfig):
    name = 'crawl'

    def ready(self):
        import crawl.signals  # Registers the signal handlers
