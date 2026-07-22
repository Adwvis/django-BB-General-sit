from django.core.management.base import BaseCommand , CommandError
from django.db import transaction
from asgiref.sync import sync_to_async
import asyncio
import httpx
from datetime import datetime
import time
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.db.models import Q

semaphore = asyncio.Semaphore(15)

# region issuning order detail


async def get_paid_detail(uid):
    async with semaphore:
        x = 0
        while True:
            try:
                print("start get_order_detail +")
                url = f"https://bimebazar.com/api/issue/orders/{uid}/"

                token = "c3dcc40f764ee7d6f1cb72c65d67d360b81d6712"

                headers = {
                    "Authorization": f"Token {token}"
                }

                async with httpx.AsyncClient(follow_redirects=True,timeout=30) as client:
                    response = await client.get(url, headers=headers)

                print("Status:", response.status_code , uid)

                if response.status_code == 200:
                    data = response.json()
                    # print(data)
                    return data
                else:
                    print(response.text)
            except Exception as e:
                if x == 5:
                    break
                x +=1
                print("get_order_detail: ",e)


        
@sync_to_async
def filtered_issuing_order():
    help = "This def findes available agents and filters orders that are in issuing of available agents" 
    from accounts.models import ProfileThpIssuingAgent
    from thirdparty.models import ThpIssuingInIssuingOrder

    present_agents = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),is_working = True , is_visible= True).values("person_name",)
    # filtered_orders = ThpIssuingInIssuingOrder.objects.filter(issuing_agent_name__in=present_agents, Q(is_issuing=True) | Q(is_issuing__isnull=True)).values("tracking_code","uid")
    filtered_orders = ThpIssuingInIssuingOrder.objects.filter(Q(is_issuing=True) | Q(is_issuing__isnull=True),issuing_agent_name__in=present_agents).values("tracking_code", "uid")
    print(present_agents)
    print("-"*100)
    print(filtered_orders)
    return list(filtered_orders)

@sync_to_async
def bulk_update_issuing_orders(objects):
    from thirdparty.models import ThpIssuingInIssuingOrder
    with transaction.atomic():
        ThpIssuingInIssuingOrder.objects.bulk_update(
            objects,
            fields=[
                "is_issuing",
            ],
        )


async def calling_issuing_order_detail():
    await specify_issuing_agent_name()
    issuing_filtered_order = await filtered_issuing_order()

    issuing_details_task = [get_paid_detail(item["uid"]) for item in issuing_filtered_order ]   
    issuing_details = await asyncio.gather(*issuing_details_task)

    from thirdparty.models import ThpIssuingInIssuingOrder
    objects = []
    for item in issuing_details:
        is_issuing = item["policy"]["insurance_number"] is None
        obj = ThpIssuingInIssuingOrder(
            tracking_code= item["tracking_code"],
            is_issuing= is_issuing,
        )
        objects.append(obj)

    await bulk_update_issuing_orders(objects)

# endregion

@sync_to_async
def specify_issuing_agent_name():
    help = "This def is for updateing names in ThpIssuingInIssuingOrder table (joins issuing_agent_id to AuthUser tables and write it on ThpIssuingInIssuingOrder)"

    from accounts.models import AuthUserBackOffice
    from thirdparty.models import ThpIssuingInIssuingOrder
    ThpIssuingInIssuingOrder.objects.update(
    issuing_agent_name=Subquery(
        AuthUserBackOffice.objects.filter(
            id=OuterRef("issuing_agent_id")
        ).values("first_name")[:1]))
    
    # UPDATE issuing_list
    #     SET agent_name = (
    #         SELECT first_name
    #         FROM auth_user
    #         WHERE auth_user.id = issuing_list.agent_id
    #         LIMIT 1
    #     );



class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        asyncio.run(calling_issuing_order_detail())
        # print(filtered_issuing_order()[0]['person_name'])
        # filtered_issuing_order()