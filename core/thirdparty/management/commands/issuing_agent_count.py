from celery import shared_task
# from django_redis import get_redis_connection
from django.db import transaction , connection
from asgiref.sync import sync_to_async
from django.db.models import OuterRef, Subquery , Q , Count, CharField , Aggregate , F
from django.utils import timezone
import redis


import asyncio
import httpx
from datetime import datetime
import time

from django.core.management.base import BaseCommand


def agents_issuing_counts():
    from django.contrib.postgres.aggregates import StringAgg
    from django.db.models.functions import Cast
    from django.db.models import CharField
    from thirdparty.models import ThpIssuingOrder
    from accounts.models import ProfileThpIssuingAgent
    from collections import defaultdict


    # present_agents = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),is_working = True , is_visible= True).values("person_name",)
    present_agents = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),is_working = True , is_visible= True)

    result = (
        ThpIssuingOrder.objects
        .filter(is_issuing=True,state_name = "issuing",chosen_issuing_agent_name__in = present_agents)
        .values("chosen_issuing_agent_name")
        .annotate(
            count_=Count("tracking_code"),
            companies=StringAgg("company_name", delimiter=", ", ordering="company_name"),
            tracking_code=StringAgg(Cast("tracking_code", CharField()), delimiter=", ", ordering="company_name"),
        )
    )

    updated_agent_ids = []

    for item in result:
        updated_agent_ids.append(item["chosen_issuing_agent_name"])

        agent_instance = ProfileThpIssuingAgent.objects.filter(id=item["chosen_issuing_agent_name"]).first()
        companies = (item["companies"] or "").split(", ")
        tracking_codes = (item["tracking_code"] or "").split(", ")

        data = defaultdict(list)
        for company, code in zip(companies, tracking_codes):
            data[company].append(code)

        agent_instance.orders_in_issuing = dict(data)
        agent_instance.assigned_order = (item["count_"])
        agent_instance.save()

    present_agents.exclude(id__in=updated_agent_ids).update(orders_in_issuing={},assigned_order=0)



class Command(BaseCommand):
    # help = "Update paid orders"

    def handle(self, *args, **options):
        agents_issuing_counts()