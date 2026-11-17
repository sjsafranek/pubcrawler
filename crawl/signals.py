from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

# from .models import City
# from .tasks import process_new_city


# @receiver(post_save, sender=City)
# def trigger_pub_search_task(sender, instance, created, **kwargs):
#     if created:
#         transaction.on_commit(lambda: process_new_city.enqueue(instance.id))

