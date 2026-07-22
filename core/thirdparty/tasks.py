from celery import shared_task
# from django_redis import get_redis_connection
from django.db import transaction , connection
from asgiref.sync import sync_to_async
from django.db.models import OuterRef, Subquery , Q , Count, CharField , Aggregate , F
from django.utils import timezone
from django.forms.models import model_to_dict
import redis

import asyncio
import httpx
from datetime import datetime
import time


redis_client = redis.Redis(
    host="redis-bb",
    port=6379,
    db=0
)

@shared_task
def t_test():

    print(f"t_task-------------{datetime.now()}")
    time.sleep(2)

@shared_task
def check_active_assignments():

    lock = redis_client.lock(
        "assignment_check_lock",
        timeout=300,
        blocking=False,
    )

    acquired = lock.acquire()

    if not acquired:
        print(
            "Last task is ongoing"
        )
        return

    try:
        for i in range(60):
            print(f"for loop index:, {i}, {datetime.now()}")
            time.sleep(1)

    finally:
        lock.release()

# region week day ------------------------
def week_day():
    today_weekday = datetime.now().weekday()
    iran_weekday = (today_weekday + 2) % 7
    return iran_weekday

# region issuing_list ----------------------------------------------------------------------------------------------------------------------------------

def flatten_issuing_list(item):
    return {
        "order_id": item["id"],
        "tracking_code": item["tracking_code"],
        "uid": item["uid"],
        "state_id": item["state"]["id"],
        "state_name": item["state"]["name_en"],
        "company_id": item["company"]["id"],
        "company_name": item["company"]["name_en"],
        "issuing_agent_id": item["agent_id"],
        "order_id": item["id"],

    }


async def get_issuing_list(limit,offset=0):
    url = "https://bimebazar.com/api/issue/orders/"
    params = {
        "insurance_type": "thirdparty",
        # "state": "paid",
        "state": "issuing",
        "limit": limit,
        "offset": offset,
        "state_canceled": "no_request"
    }
    token = "c3dcc40f764ee7d6f1cb72c65d67d360b81d6712"
    headers = {"Authorization": f"Token {token}"}
    async with httpx.AsyncClient(follow_redirects=True,timeout=60) as client:
        response = await client.get(url, headers=headers , params=params)

    if response.status_code == 200:
        data = response.json()
        return data["results"]
    else:
        print(response.text)

@sync_to_async
def database_process_issuing_list(unique_data, new_tracking_code):
    # from .models import ThpIssuingInIssuingOrder
    from .models import ThpIssuingOrder
    
    with transaction.atomic():
        existing_tracking_code = set(str(tc) for tc in ThpIssuingOrder.objects.filter(state_name="issuing").values_list('tracking_code', flat=True))
        print(f"{len(existing_tracking_code)} Issuing Exist")
        to_insert = [item for item in unique_data if str(item["tracking_code"]) not in existing_tracking_code]
        to_insert_tracking_codes = [item["tracking_code"] for item in to_insert]
        to_delete_existing_to_insert_order = set(str(tc) for tc in ThpIssuingOrder.objects.filter(tracking_code__in=to_insert_tracking_codes,state_name="paid").values_list('tracking_code', flat=True))

        to_delete = existing_tracking_code - new_tracking_code

        if to_delete:
            print(f"{len(to_delete)} Issuing Deleted")
            ThpIssuingOrder.objects.filter(tracking_code__in=to_delete).delete()

        if to_delete_existing_to_insert_order:
            print(f"{len(to_delete_existing_to_insert_order)} Issuing to_delete_existing_to_insert_order")
            ThpIssuingOrder.objects.filter(tracking_code__in=to_delete_existing_to_insert_order).delete()


        if to_insert:
            print(f"{len(to_insert)} Issuing Inserted")
            ThpIssuingOrder.objects.bulk_create([
                ThpIssuingOrder(**item) for item in to_insert
            ])

async def calling_issuing_list(limit):
    print("start calling issuing list")
    while True:
        try:
            all_issuing_list = []
            x = 0
            while True:
                issuing_list = await get_issuing_list(limit,limit*x)
                all_issuing_list += issuing_list
                print(f"len all_issuing_list : {len(all_issuing_list)}")
                if  len(issuing_list) == limit:
                    x += 1
                else:
                    data = [flatten_issuing_list(item) for item in all_issuing_list]
                    unique_data = list({item['tracking_code']: item for item in data}.values())
                    new_tracking_code = {str(item["tracking_code"]) for item in unique_data}
                    await database_process_issuing_list(unique_data, new_tracking_code)
                    return
        except Exception as e:
            print(f"Issuning list Error:  {e}")
# endregion

# region order_list
def flatten_paid_list(item):
    return {
        "order_id": item["id"],
        "tracking_code": item["tracking_code"],
        "uid": item["uid"],
        "state_id": item["state"]["id"],
        "state_name": item["state"]["name_en"],
        "issuing_agent_id": item["agent_id"],
        "company_id": item["company"]["id"],
        "company_name": item["company"]["name_en"],
    }

@sync_to_async
def database_process_paid_list(unique_data, new_tracking_code):
    from .models import ThpIssuingOrder
    
    with transaction.atomic():
        existing_tracking_code = set(str(tc) for tc in ThpIssuingOrder.objects.filter(state_name="paid").values_list('tracking_code', flat=True))
        print(f"{len(existing_tracking_code)} Issuing Exist")
        to_insert = [item for item in unique_data if str(item["tracking_code"]) not in existing_tracking_code]
        to_insert_tracking_codes = [item["tracking_code"] for item in to_insert]
        to_delete_existing_to_insert_order = set(str(tc) for tc in ThpIssuingOrder.objects.filter(tracking_code__in=to_insert_tracking_codes,state_name="issuing").values_list('tracking_code', flat=True))

        to_delete = existing_tracking_code - new_tracking_code
        

        if to_delete:
            print(f"{len(to_delete)} Issuing Deleted")
            ThpIssuingOrder.objects.filter(tracking_code__in=to_delete).delete()

        if to_delete_existing_to_insert_order:
            print(f"{len(to_delete_existing_to_insert_order)} Issuing to_delete_existing_to_insert_order")
            ThpIssuingOrder.objects.filter(tracking_code__in=to_delete_existing_to_insert_order).delete()


        if to_insert:
            print(f"{len(to_insert)} Issuing Inserted")
            ThpIssuingOrder.objects.bulk_create([
                ThpIssuingOrder(**item) for item in to_insert
            ])

async def get_paid_list(limit,offset=0):
    url = "https://bimebazar.com/api/issue/orders/"
    params = {
        "insurance_type": "thirdparty",
        "state": "paid",
        # "state": "issuing",
        "limit": limit,
        "offset": offset,
        "state_canceled": "no_request"
    }
    token = "c3dcc40f764ee7d6f1cb72c65d67d360b81d6712"
    headers = {"Authorization": f"Token {token}"}
    async with httpx.AsyncClient(follow_redirects=True,timeout=60) as client:
        response = await client.get(url, headers=headers , params=params)

    if response.status_code == 200:
        data = response.json()
        return data["results"]
    else:
        print(response.text)

async def calling_paid_list(limit):
    print("start calling paid list")
    while True:
        try:
            all_paid_list = []
            x = 0
            while True:
                paid_list = await get_paid_list(limit,limit*x)
                all_paid_list += paid_list
                print(f"len all_paid_list : {len(all_paid_list)}")
                if  len(paid_list) == limit:
                    x += 1
                else:
                    data = [flatten_paid_list(item) for item in all_paid_list]
                    unique_data = list({item['tracking_code']: item for item in data}.values())
                    new_tracking_code = {str(item["tracking_code"]) for item in unique_data}
                    await database_process_paid_list(unique_data, new_tracking_code)
                    return
        except Exception as e:
            print(f"Issuning list Error: {e}")

# endregion

# region paid order detail

async def get_paid_detail(semaphore_paid_detail,uid):

    async with semaphore_paid_detail:
        x = 0
        while True:
            try:
                print("start get_paid_order_detail +")
                url = f"https://bimebazar.com/api/issue/orders/{uid}/"

                token = "c3dcc40f764ee7d6f1cb72c65d67d360b81d6712"

                headers = {
                    "Authorization": f"Token {token}"
                }

                async with httpx.AsyncClient(follow_redirects=True,timeout=30) as client:
                    response = await client.get(url, headers=headers)

                print(f"Status: {response.status_code} - {uid}")

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
                print(f"get_paid_order_detail: {e}")

@sync_to_async
def bulk_update_paid_orders(objects):
    from thirdparty.models import ThpIssuingOrder
    with transaction.atomic():
        ThpIssuingOrder.objects.bulk_update(
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
    from thirdparty.models import ThpIssuingOrder
    with transaction.atomic():
        unique_companies = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),
        is_working = True , is_visible= True, working_days__contains=[week_day()]).values_list("working_insurance_company__name",flat=True,).distinct()
        paid_filtered_order = ThpIssuingOrder.objects.filter(
        state_name="paid",company_name__in=unique_companies,first_paid_date__isnull=True,).values("tracking_code","uid",)
        return list(paid_filtered_order)

async def calling_paid_order_detail():
    from thirdparty.models import ThpIssuingOrder
    paid_filtered_order = await filtered_paid_order_def()
    semaphore_paid_detail = asyncio.Semaphore(15)
    paid_details_task = [get_paid_detail(semaphore_paid_detail,item["uid"]) for item in paid_filtered_order ]   
    paid_details = await asyncio.gather(*paid_details_task)

    objects = []
    for item in paid_details:
        sanhab_info = item["last_policy"]["sanhab_info"] is not None
        first_paid_date_str = item["payment"]["first_paid_date"]
        str_state_logs = str(item["state_logs"])
        corection_loop = (str_state_logs.count("user_wrong_data") + str_state_logs.count("need_postal_code"))
        # not_fresh_states = ["user_wrong_data","need_postal_code","safe_correction_need","correction_need","submitted_to_branch","license_required",]
        not_fresh_states = ["user_wrong_data","license_required",]
        is_fresh = not any(state in str_state_logs for state in not_fresh_states)
        obj = ThpIssuingOrder(
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

# region issuing order detail

async def get_issuing_detail(semaphore_issuing_detail,uid):
    
    async with semaphore_issuing_detail:
        x = 0
        while True:
            try:
                print("start get_issuing_order_detail +")
                url = f"https://bimebazar.com/api/issue/orders/{uid}/"

                token = "c3dcc40f764ee7d6f1cb72c65d67d360b81d6712"

                headers = {
                    "Authorization": f"Token {token}"
                }

                async with httpx.AsyncClient(follow_redirects=True,timeout=30) as client:
                    response = await client.get(url, headers=headers)

                print(f"Status: {response.status_code} - {uid}")

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
                print(f"get_issuing_order_detail: {e}")


        
@sync_to_async
def filtered_issuing_order():
    help = "This def findes available agents and filters orders that are in issuing of available agents" 
    from accounts.models import ProfileThpIssuingAgent
    from thirdparty.models import ThpIssuingOrder

    present_agents = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),
                                                           working_days__contains=[week_day()],is_working = True , is_visible= True)
    filtered_orders = ThpIssuingOrder.objects.filter(Q(is_issuing=True) | Q(is_issuing__isnull=True),state_name = "issuing",chosen_issuing_agent_name__in=present_agents).values("tracking_code", "uid")
    print(present_agents)
    print("-"*100)
    print(filtered_orders)
    return list(filtered_orders)

@sync_to_async
def bulk_update_issuing_orders(objects):
    from thirdparty.models import ThpIssuingOrder
    with transaction.atomic():
        ThpIssuingOrder.objects.bulk_update(
            objects,
            fields=[
                "exp_date",
                "first_paid_date",
                "sanhab_info",
                "installment_type",
                "partner",
                "corection_loop",
                "is_issuing",
                "last_action",
            ],
        )


async def calling_issuing_order_detail():
    await specify_issuing_agent_name()
    issuing_filtered_order = await filtered_issuing_order()
    semaphore_issuing_detail = asyncio.Semaphore(15)
    issuing_details_task = [get_issuing_detail(semaphore_issuing_detail,item["uid"]) for item in issuing_filtered_order ]   
    issuing_details = await asyncio.gather(*issuing_details_task)

    from thirdparty.models import ThpIssuingOrder
    objects = []
    for item in issuing_details:
        sanhab_info = item["last_policy"]["sanhab_info"] is not None
        first_paid_date_str = item["payment"]["first_paid_date"]
        str_state_logs = str(item["state_logs"])
        corection_loop = (str_state_logs.count("user_wrong_data") + str_state_logs.count("need_postal_code"))
        is_issuing = item["policy"]["insurance_number"] is None
        last_action_srt = item["state_logs"][0]["created_date"]
        obj = ThpIssuingOrder(
            tracking_code= item["tracking_code"],
            exp_date= (datetime.strptime(item["last_policy"]["expiration_date"], "%Y-%m-%d").date()
                if item.get("last_policy") and item["last_policy"].get("expiration_date") else None),
            first_paid_date= datetime.fromisoformat(first_paid_date_str.replace("Z", "+00:00")) if first_paid_date_str else None,
            sanhab_info= sanhab_info,
            installment_type= item["payment"]["installment_type"],
            partner= item["partner"]["name_en"],
            corection_loop= corection_loop,
            is_issuing= is_issuing,
            last_action = datetime.fromisoformat(last_action_srt.replace("Z", "+00:00")) if first_paid_date_str else None,
        )
        objects.append(obj)

    await bulk_update_issuing_orders(objects)

# endregion

@sync_to_async
def specify_issuing_agent_name():
    help = "This def is for updateing names in ThpIssuingInIssuingOrder table (joins issuing_agent_id to AuthUser tables and write it on ThpIssuingInIssuingOrder)"

    from accounts.models import AuthUserBackOffice , ProfileThpIssuingAgent
    from thirdparty.models import ThpIssuingOrder

    ThpIssuingOrder.objects.filter(issuing_agent_id__isnull=False,state_name= "issuing").update(
        chosen_issuing_agent_name=Subquery(
            ProfileThpIssuingAgent.objects.filter(
                person_name=Subquery(
                    AuthUserBackOffice.objects.filter(
                        id=OuterRef(OuterRef("issuing_agent_id"))
                    ).values("first_name")[:1]
                )
            ).values("id")[:1]
        )
    )

# endregion

# region search agent in auth user
@sync_to_async
def search_agent_in_auth_user():
    from accounts.models import ProfileThpIssuingAgent , WorkingInsuranceCompanies , AuthUserBackOffice
    
    agents_list = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),
    working_days__contains=[week_day()],is_working = True , is_visible= True).values("person_name","working_insurance_company__name",
                                                                                     "working_insurance_company__last_name",)

    for agent in agents_list:
        res = AuthUserBackOffice.objects.filter(first_name=agent["person_name"],last_name=agent["working_insurance_company__last_name"]).all()
        if not res.exists():
            agent_instance = ProfileThpIssuingAgent.objects.filter(person_name=agent["person_name"]).first()
            company = WorkingInsuranceCompanies.objects.filter(name=agent["working_insurance_company__name"]).first()
            if agent_instance and company:
                agent_instance.working_insurance_company.remove(company)

# endregion



# region agents issuing counts
# class GroupConcat(Aggregate):
#     function = "GROUP_CONCAT"
#     template = "%(function)s(%(expressions)s, '%(separator)s')"
#     output_field = CharField()

#     def __init__(self, expression, separator=", ", **extra):
#         super().__init__(expression, separator=separator, **extra)

@sync_to_async
def agents_issuing_counts():
    from django.contrib.postgres.aggregates import StringAgg
    from django.db.models.functions import Cast
    from django.db.models import CharField
    from thirdparty.models import ThpIssuingOrder
    from accounts.models import ProfileThpIssuingAgent
    from collections import defaultdict


    present_agents = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),
                                                           working_days__contains=[week_day()],is_working = True , is_visible= True)

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

        agent_instance = ProfileThpIssuingAgent.objects.filter(is_working=True,is_visible=True,start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),
                                                               working_days__contains=[week_day()],id=item["chosen_issuing_agent_name"]).first()
        companies = (item["companies"] or "").split(", ")
        tracking_codes = (item["tracking_code"] or "").split(", ")

        data = defaultdict(list)
        for company, code in zip(companies, tracking_codes):
            data[company].append(code)

        agent_instance.orders_in_issuing = dict(data)
        agent_instance.assigned_order = (item["count_"])
        agent_instance.save()

    present_agents.exclude(id__in=updated_agent_ids).update(orders_in_issuing="",assigned_order=0)

        

# endregion


# region reassing

async def chang_state_in_back_office_to_paid(item,client,semaphore,bb_login_csrftoken):
    async with semaphore:
        try:
            change_state_url= f"https://bimebazar.com/panel/orders/change-state/{item.uid}/"
            change_state_data = {
            "csrfmiddlewaretoken": bb_login_csrftoken,
            "transition": "131",
            'activate_messaging': 'on',           
            'activate_recalculate': 'on',          
            'deactivation_timeout': '60',  }
            change_state_headers = {
            "Referer": change_state_url,
            }
            
            response_change_state = await client.post(change_state_url, data=change_state_data, headers=change_state_headers)
            if response_change_state.status_code != 200:
                print(f"Unexpected status {response_change_state.status_code} for {item.tracking_code}")
        except Exception as e:
            print(f"chang state in back office to paid Error tracking_code={item.tracking_code},{e}")

async def find_chang_state_in_back_office_to_paid(reassing_order):
    res_check_bimebazar_login_token = await check_bimebazar_login_token()

    if res_check_bimebazar_login_token == "token expired":
        res_update_now_bimebazar_token = await update_now_bimebazar_token()

        if res_update_now_bimebazar_token == "Error":
            print("update_now_bimebazar_token Error No order Assinged",)
            return
        
    elif res_check_bimebazar_login_token == "Error":
        print("check_bimebazar_login_token Error No order Assinged",)
        return

    from accounts.models import ForeignLoginToken

    bb_login_auth_token = await sync_to_async(
        lambda: ForeignLoginToken.objects.filter(name="bime-bazar-auth-token", tag="auth-token").first())()
    bb_login_csrftoken = await sync_to_async(
        lambda: ForeignLoginToken.objects.filter(name="bime-bazar-csrftoken", tag="csrftoken").first())()

    semaphore = asyncio.Semaphore(15)


    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        client.cookies.set("auth-token", bb_login_auth_token.token,domain="bimebazar.com")
        client.cookies.set("csrftoken", bb_login_csrftoken.token,domain="bimebazar.com")

        tasks = [
            chang_state_in_back_office_to_paid(item=item,client=client,semaphore=semaphore,bb_login_csrftoken=bb_login_csrftoken.token)
            for item in reassing_order]
        
        await asyncio.gather(*tasks)


@sync_to_async
def get_reassign_orders():
    from thirdparty.models import ThpIssuingOrder, ThpIssuingOrderLog
    from datetime import timedelta
    from django.utils import timezone

    one_hour_ago = timezone.now() - timedelta(hours=1)

    with transaction.atomic():
        orders = ThpIssuingOrder.objects.filter(
            last_action__isnull=False,
            last_action__lt=one_hour_ago,
            state_name="issuing",
            is_issuing=True
        )
        data = list(orders.values())
        for d in data:
            d['assigned_from_id'] = d.get('chosen_issuing_agent_name_id')
            d['assignment_status'] = "reassigned"
            d["chosen_issuing_agent_name_id"] = None
        ThpIssuingOrderLog.objects.bulk_create(
            [ThpIssuingOrderLog(**d) for d in data], batch_size=500
        )
        for item in orders:
            agent = item.chosen_issuing_agent_name
            # print(item.tracking_code, agent.person_name, agent.capacity)
            if agent.capacity == 0:
                continue
            
            agent.capacity -= 1
            agent.save(update_fields=["capacity"])

        orders.update(
            state_name="paid", state_id=23,
            chosen_issuing_agent_auth_user_id=None,
            chosen_issuing_agent_name=None,
            assignment_status="reassigned"
        )
        return list(orders)

async def find_reassine():
    orders = await get_reassign_orders()
    await find_chang_state_in_back_office_to_paid(orders)


# endregion

# region score
@sync_to_async
def score():

    with connection.cursor() as cursor:
        # cursor.execute("SELECT * FROM thirdparty_thpissuinginpaidorder WHERE is_fresh = True")
        cursor.execute("""
            WITH scoring AS (
            SELECT
                order_id,
                tracking_code,
                uid,
                state_name,
                company_name,
                exp_date,
                first_paid_date,
                sanhab_info,
                installment_type,
                partner,
                corection_loop,
                is_fresh,
                assignment_status,
            -- ========== C1: Risk Score (وزن 0.4) ==========
            (
            -- Expiration Risk (وزن 0.3)
            (CASE
                WHEN exp_date < DATE(first_paid_date) THEN 1
                WHEN exp_date = DATE(first_paid_date) THEN 0.6
                ELSE 0.2
            END) * 0.3
            +
            -- Time to SLA Breach (وزن 0.3)
            (1 - LEAST(
                CASE
                WHEN EXTRACT(HOUR FROM first_paid_date) < 21 THEN
                    EXTRACT(EPOCH FROM (DATE(first_paid_date) + INTERVAL '1 day' + TIME '21:00:00' - NOW())) / 3600
                ELSE
                    EXTRACT(EPOCH FROM (DATE(first_paid_date) + INTERVAL '2 days' + TIME '21:00:00' - NOW())) / 3600
                END / 48.0,
                1
            )) * 0.3
            +
            -- Paid Recency (وزن 0.2)
            LEAST(EXTRACT(EPOCH FROM (NOW() - first_paid_date)) / 3600 / 48.0, 1) * 0.2
            +
            -- Sanhab Status (وزن 0.1)
            case	when sanhab_info = true then 1 else 0 end * 0.1
            +
            -- Payment Type (وزن 0.1)
            (CASE installment_type
                WHEN 'cash' THEN 0.3
                WHEN 'bnpl' THEN 0.75
                WHEN 'bb_bnpl' THEN 1
                ELSE 0
            END) * 0.1
            ) AS c1_risk,

            -- ========== C2: Channel Score (وزن 0.3) ==========
            (CASE
            WHEN partner NOT IN ('autoabzar', 'snappbimeh', 'app', 'mashhad', 'tapsi') THEN
                CASE partner
                WHEN 'mashad' THEN 1
                WHEN 'snappbimeh' THEN 0.6
                WHEN 'tapsi' THEN 0.6
                ELSE 0.3
                END
            ELSE
                CASE partner
                WHEN 'mashhad' THEN 1
                WHEN 'snappbimeh' THEN 0.6
                WHEN 'tapsi' THEN 0.6
                ELSE 0.3
                END
            END) AS c2_channel,

            -- ========== C3: Process Score (وزن 0.2) ==========
            (
            -- Time Since Paid (وزن 0.4)
            LEAST(EXTRACT(EPOCH FROM (NOW() - first_paid_date)) / 3600 / 48.0, 1) * 0.4
            +
            -- Payment Time (9PM) (وزن 0.15)
            (CASE WHEN EXTRACT(HOUR FROM first_paid_date) >= 21 THEN 0 ELSE 1 END) * 0.15
            +
            -- Loop Count (وزن 0.3)
            LEAST(corection_loop / 2.0, 1) * 0.3
            ) AS c3_process,

            -- ========== C4: Type Score (وزن 0.1) ==========
            (CASE WHEN is_fresh = true THEN 1 ELSE 0 END) AS c4_type
            FROM thirdparty_thpissuingorder
            where partner not in ('bbseller','bbseller_snapp','bbseller_org')
            and state_name = 'paid')


            UPDATE thirdparty_thpissuingorder t
            SET score = ROUND(
            (0.4 * s.c1_risk + 0.3 * s.c2_channel + 0.2 * s.c3_process + 0.1 * s.c4_type)::numeric,
            4
            )
            FROM scoring s
            WHERE t.order_id = s.order_id;
                    """)
        # rows = cursor.fetchall()
        # print(rows)


# endregion


# region preassing
@sync_to_async
def preassing():
    from thirdparty.models import ThpIssuingOrder , ThpIssuingOrderLog
    from accounts.models import ProfileThpIssuingAgent , AuthUserBackOffice , WorkingInsuranceCompanies
    ThpIssuingOrder.objects.filter(state_name = "paid",chosen_issuing_agent_name__isnull=False).update(chosen_issuing_agent_name=None)

    paid_order_list =  ThpIssuingOrder.objects.filter(state_name="paid",score__isnull = False, chosen_issuing_agent_name__isnull = True).order_by("-score")

    if not paid_order_list:
        print("paid_order_list is empty")
        return
    
    for item in paid_order_list:
        # print(item.score)
        
        work_group_needed = ["fresh" if item.is_fresh else "secondary"]

        if item.assignment_status == "reassigned":
            excluded_agent_id = ThpIssuingOrderLog.objects.filter(tracking_code="9708222",assignment_status="reassigned").values("assigned_from_id")

            right_agents = (
                ProfileThpIssuingAgent.objects
                .filter(working_insurance_company__name=item.company_name)
                .filter(working_category__name__in=work_group_needed)
                .filter(capacity__gt=F("assigned_order"))
                .filter(is_working = True , is_visible= True)
                .filter(working_days__contains=[week_day()])
                .exclude(id__in=excluded_agent_id)
                .order_by("assigned_order")
            )

        else:

            right_agents = (
                ProfileThpIssuingAgent.objects
                .filter(working_insurance_company__name=item.company_name)
                .filter(working_category__name__in=work_group_needed)
                .filter(capacity__gt=F("assigned_order"))
                .filter(is_working = True , is_visible= True)
                .filter(working_days__contains=[week_day()])
                .order_by("assigned_order")
            )

        agent = right_agents.first()
        # print(agent)
        if agent is None:
            continue
        
        company_last_name = WorkingInsuranceCompanies.objects.filter(name=item.company_name).first()
        auth_user_company_id = AuthUserBackOffice.objects.filter(first_name=agent.person_name, last_name = company_last_name.last_name).first()

        with transaction.atomic():
            item.chosen_issuing_agent_name = agent
            item.chosen_issuing_agent_auth_user_id = auth_user_company_id.id
            agent.assigned_order = F("assigned_order") + 1  
            item.save()
            agent.save()
        
# endregion

# login and assingment region

async def update_now_bimebazar_token():
    x = 0
    LOGIN_URL = "https://bimebazar.com/accounts/panel-login/"

    while x <= 3:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                await client.get(LOGIN_URL)

                login_data = {
                    "csrfmiddlewaretoken": client.cookies.get("csrftoken"),
                    "username": "hosain.kazmi_aa",
                    "password": "fg123456",
                }

                login_response = await client.post(LOGIN_URL,data=login_data,headers={"Referer": LOGIN_URL},)

                if (login_response.status_code == 200 and client.cookies.get("csrftoken") and client.cookies.get("auth-token")):
                    from accounts.models import ForeignLoginToken

                    auth_token = client.cookies.get("auth-token")

                    await sync_to_async(
                        lambda: ForeignLoginToken.objects.filter(name="bime-bazar-auth-token", tag="auth-token").update(token=auth_token))()
                    await sync_to_async(
                        lambda: ForeignLoginToken.objects.filter(name="bime-bazar-csrftoken", tag="csrftoken").update(token=client.cookies.get("csrftoken")))()
                    return "Ok"

        except Exception as e:
            print(f"update_now_bimebazar_token {e}")

        x += 1

    return "Error"


async def check_bimebazar_login_token():
    from bs4 import BeautifulSoup
    x = 0
    while x <= 3:
        try:
            from accounts.models import ForeignLoginToken

            bb_login_token = await sync_to_async(
                lambda: ForeignLoginToken.objects.filter(name="bime-bazar-auth-token", tag="auth-token").first())()

            if bb_login_token is None:
                return "Error"

            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                client.cookies.set("auth-token", bb_login_token.token, domain="bimebazar.com")
                response = await client.get("https://bimebazar.com/panel/")

            soup = BeautifulSoup(response.text, "html.parser")
            input_tag = soup.find("input", {"id": "id_username"})
            # print(bb_login_token.token if input_tag is None else "token expired")

            if input_tag is None:
                await sync_to_async(lambda: 
                    ForeignLoginToken.objects.filter(name="bime-bazar-csrftoken", tag="csrftoken").update(token=client.cookies.get("csrftoken")))()
                return "Ok"
            else:
                return "token expired"

            

        except Exception as e:
            print(f"check_bimebazar_login_token Error {e}")
            x += 1

    return "Error"

async def assing(item,client,semaphore,bb_login_csrftoken):
    async with semaphore:
        try:
            from thirdparty.models import ThpIssuingOrder , ThpIssuingOrderLog

            choose_agent_url = "https://bimebazar.com/panel/user-order-assignment/create/"
            choose_agent_data = {
            "csrfmiddlewaretoken": bb_login_csrftoken,
            "user": item.chosen_issuing_agent_auth_user_id,
            "order": item.order_id}
            choose_agent_headers = {
            "Referer": choose_agent_url,
            }
            response_asine = await client.post(choose_agent_url, data=choose_agent_data, headers=choose_agent_headers)


            change_state_url= f"https://bimebazar.com/panel/orders/change-state/{item.uid}/"
            change_state_data = {
            "csrfmiddlewaretoken": bb_login_csrftoken,
            "transition": "57",
            'activate_messaging': 'on',           
            'activate_recalculate': 'on',          
            'deactivation_timeout': '60',  }
            change_state_headers = {
            "Referer": change_state_url,
            }
            
            response_change_state = await client.post(change_state_url, data=change_state_data, headers=change_state_headers)

            if response_asine.status_code != 200:
                response_asine = await client.post(choose_agent_url, data=choose_agent_data, headers=choose_agent_headers)

            if response_asine.status_code == 200 and response_change_state.status_code == 200:

                await sync_to_async(lambda:
                ThpIssuingOrder.objects.filter(tracking_code=item.tracking_code)
                .update(state_name="issuing", state_id=23))()

                if item.assignment_status == "reassigned":

                    await sync_to_async(lambda:
                    ThpIssuingOrderLog.objects.filter(
                        tracking_code=item.tracking_code,
                        assigned_from__isnull=False,
                        chosen_issuing_agent_name__isnull=True
                    ).update(chosen_issuing_agent_name=item.chosen_issuing_agent_name))()

                else:

                    data = await sync_to_async(model_to_dict)(item)
                    data["chosen_issuing_agent_name_id"] = data.pop("chosen_issuing_agent_name")
                    await sync_to_async(lambda: 
                        ThpIssuingOrderLog.objects.create(**data))()
                
                
        except Exception as e:
            print(f"assing Error tracking_code={item.tracking_code},{e}")

async def assingment():

    res_check_bimebazar_login_token = await check_bimebazar_login_token()

    if res_check_bimebazar_login_token == "token expired":
        res_update_now_bimebazar_token = await update_now_bimebazar_token()

        if res_update_now_bimebazar_token == "Error":
            print("update_now_bimebazar_token Error No order Assinged",)
            return
        
    elif res_check_bimebazar_login_token == "Error":
        print("check_bimebazar_login_token Error No order Assinged",)
        return

    from thirdparty.models import ThpIssuingOrder
    from accounts.models import ForeignLoginToken

    bb_login_auth_token = await sync_to_async(
        lambda: ForeignLoginToken.objects.filter(name="bime-bazar-auth-token", tag="auth-token").first())()
    bb_login_csrftoken = await sync_to_async(
        lambda: ForeignLoginToken.objects.filter(name="bime-bazar-csrftoken", tag="csrftoken").first())()

    pre_assing_list = await sync_to_async(lambda:
        list(ThpIssuingOrder.objects.select_related('chosen_issuing_agent_name')
            .filter(state_name='paid', score__isnull=False, chosen_issuing_agent_name__isnull=False))
    )()

    semaphore = asyncio.Semaphore(15)

    client = httpx.AsyncClient(follow_redirects=True,timeout=30)
    client.cookies.set("auth-token", bb_login_auth_token.token,domain="bimebazar.com")
    client.cookies.set("csrftoken", bb_login_csrftoken.token,domain="bimebazar.com")
    # باید سمت assing نوشته شود و موارد یه دور چک شود

    assign_list_task = [assing(item=item,client=client,semaphore=semaphore,bb_login_csrftoken=bb_login_csrftoken.token) for item in pre_assing_list]
    await asyncio.gather(*assign_list_task)

    await client.aclose()



# endregion


async def main_thp_issuing_assignment():
    
    await asyncio.gather(
        calling_issuing_list(limit=300),
        calling_paid_list(limit=300),
    )

    await search_agent_in_auth_user()
    
    await asyncio.gather(
        calling_issuing_order_detail(),
        calling_paid_order_detail(),
    )
    await agents_issuing_counts()
    await find_reassine()
    await score()
    await preassing()
    await assingment()



@shared_task
def thp_issuing_assignment():

    lock = redis_client.lock(
        "thp_issuing_assignment",
        timeout=300,
        blocking=False,
    )

    acquired = lock.acquire()

    if not acquired:
        # print(
        #     "thp_issuing_assignment task is ongoing -------------------------------------------------------"
        # )
        return

    try:
        asyncio.run(main_thp_issuing_assignment())
    finally:
        lock.release()

# async def test_print():
    
#     from datetime import datetime
#     print(f"time is {datetime.now()} -----------------")

# # @shared_task(bind=True)
# def thp_issuing_assignment_bind(self):

#     lock = redis_client.lock(
#         "thp_issuing_assignment_bind",
#         timeout=10,
#         blocking=False,
#     )

#     if not lock.acquire():
#         self.apply_async(countdown=5)
#         return
#     check_condition_from_db = False
#     try:
#         if check_condition_from_db:
#             asyncio.run(test_print())
#     finally:
#         lock.release()

#     self.apply_async(countdown=5)