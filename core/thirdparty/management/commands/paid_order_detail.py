from django.core.management.base import BaseCommand , CommandError
from django.db import transaction
from asgiref.sync import sync_to_async
import asyncio
import httpx
from datetime import datetime
import time

semaphore = asyncio.Semaphore(15)


# region paid order detail
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
def bulk_update_paid_orders(objects):
    from thirdparty.models import ThpIssuingInPaidOrder
    with transaction.atomic():
        ThpIssuingInPaidOrder.objects.bulk_update(
            objects,
            fields=[
                "exp_date",
                "first_paid_date",
                "sanhab_info",
                "installment_type",
                "partner",
                "corection_loop",
                "is_fresh",
            ],
        )
        
@sync_to_async
def filtered_paid_order_def():
    from accounts.models import ProfileThpIssuingAgent
    from thirdparty.models import ThpIssuingInPaidOrder
    with transaction.atomic():
        unique_companies = ProfileThpIssuingAgent.objects.values_list("working_insurance_company__name", flat=True).distinct()
        paid_filtered_order = ThpIssuingInPaidOrder.objects.filter(
        state_name="paid",company_name__in=unique_companies,first_paid_date__isnull=True,).values("tracking_code","uid",)
        return list(paid_filtered_order)

async def calling_paid_order_detail():
    from thirdparty.models import ThpIssuingInPaidOrder
    paid_filtered_order = await filtered_paid_order_def()

    paid_details_task = [get_paid_detail(item["uid"]) for item in paid_filtered_order ]   
    paid_details = await asyncio.gather(*paid_details_task)

    objects = []
    for item in paid_details:
        sanhab_info = item["last_policy"]["sanhab_info"] is not None
        first_paid_date_str = item["payment"]["first_paid_date"]
        str_state_logs = str(item["state_logs"])
        corection_loop = (str_state_logs.count("user_wrong_data") + str_state_logs.count("need_postal_code"))
        not_fresh_states = ["user_wrong_data","need_postal_code","safe_correction_need","correction_need","submitted_to_branch","license_required",]
        is_fresh = not any(state in str_state_logs for state in not_fresh_states)
        obj = ThpIssuingInPaidOrder(
            tracking_code= item["tracking_code"],
            exp_date= (datetime.strptime(item["last_policy"]["expiration_date"], "%Y-%m-%d").date()
                if item.get("last_policy") and item["last_policy"].get("expiration_date") else None),
            first_paid_date= datetime.fromisoformat(first_paid_date_str.replace("Z", "+00:00")) if first_paid_date_str else None,
            sanhab_info= sanhab_info,
            installment_type= item["payment"]["installment_type"],
            partner= item["partner"]["name_en"] , 
            corection_loop= corection_loop,
            is_fresh= is_fresh,
        )
        objects.append(obj)

    await bulk_update_paid_orders(objects)
            
# endregion



class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        asyncio.run(calling_paid_order_detail())
        # asyncio.run(calling_issuing_order_detail())