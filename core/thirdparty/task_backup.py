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
            "Last task is ongoing -------------------------------------------------------"
        )
        return

    try:
        for i in range(60):
            print(f"for loop index:, {i}, {datetime.now()}")
            time.sleep(1)

    finally:
        lock.release()

# region issuing_list
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
    from .models import ThpIssuingInIssuingOrder
    
    with transaction.atomic():
        existing_tracking_code = set(str(tc) for tc in ThpIssuingInIssuingOrder.objects.values_list('tracking_code', flat=True))
        print(f"{len(existing_tracking_code)} Issuing Exist")
        to_insert = [item for item in unique_data if str(item["tracking_code"]) not in existing_tracking_code]
        to_delete = existing_tracking_code - new_tracking_code

        if to_delete:
            print(f"{len(to_delete)} Issuing Deleted")
            ThpIssuingInIssuingOrder.objects.filter(tracking_code__in=to_delete).delete()

        if to_insert:
            print(f"{len(to_insert)} Issuing Inserted")
            ThpIssuingInIssuingOrder.objects.bulk_create([
                ThpIssuingInIssuingOrder(**item) for item in to_insert
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
    from .models import ThpIssuingInPaidOrder
    
    with transaction.atomic():
        existing_tracking_code = set(str(tc) for tc in ThpIssuingInPaidOrder.objects.values_list('tracking_code', flat=True))
        print(f"{len(existing_tracking_code)} Issuing Exist")
        to_insert = [item for item in unique_data if str(item["tracking_code"]) not in existing_tracking_code]
        to_delete = existing_tracking_code - new_tracking_code

        if to_delete:
            print(f"{len(to_delete)} Issuing Deleted")
            ThpIssuingInPaidOrder.objects.filter(tracking_code__in=to_delete).delete()

        if to_insert:
            print(f"{len(to_insert)} Issuing Inserted")
            ThpIssuingInPaidOrder.objects.bulk_create([
                ThpIssuingInPaidOrder(**item) for item in to_insert
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
    semaphore_paid_detail = asyncio.Semaphore(15)
    paid_details_task = [get_paid_detail(semaphore_paid_detail,item["uid"]) for item in paid_filtered_order ]   
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
    semaphore_issuing_detail = asyncio.Semaphore(15)
    issuing_details_task = [get_issuing_detail(semaphore_issuing_detail,item["uid"]) for item in issuing_filtered_order ]   
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

# endregion

# region search agent in auth user
@sync_to_async
def search_agent_in_auth_user():
    from accounts.models import ProfileThpIssuingAgent , WorkingInsuranceCompanies , AuthUserBackOffice
    
    agents_list = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),is_working = True , is_visible= True).values("person_name","working_insurance_company__name","working_insurance_company__last_name",)

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
    print("agents_issuing_counts-----------------")
    from django.contrib.postgres.aggregates import StringAgg
    from django.db.models.functions import Cast
    from django.db.models import CharField
    from thirdparty.models import ThpIssuingInIssuingOrder
    from accounts.models import ProfileThpIssuingAgent
    present_agents = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),is_working = True , is_visible= True).values("person_name",)

    result = (
        ThpIssuingInIssuingOrder.objects
        .filter(is_issuing=True,issuing_agent_name__in = present_agents)
        .values("issuing_agent_name")
        .annotate(
            count_=Count("tracking_code"),
            companies=StringAgg("company_name", delimiter=", ", ordering="company_name"),
            tracking_code=StringAgg(Cast("tracking_code", CharField()), delimiter=", ", ordering="company_name"),
        )
    )

    print("agents_issuing_counts-----------------2")
    for item in result:
        print(item)
        agent_instance = ProfileThpIssuingAgent.objects.filter(person_name=item["issuing_agent_name"]).first()
        companies = (item["companies"] or "").split(", ")
        tracking_codes = (item["tracking_code"] or "").split(", ")
        agent_instance.orders_in_issuing = list(zip(companies, tracking_codes))
        # agent_instance.orders_in_issuing = (item["companies"] + item["tracking_code"])
        agent_instance.assigned_order = (item["count_"])
        agent_instance.save()
        

# endregion


# region score
@sync_to_async
def scoreing():
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
                FROM thirdparty_thpissuinginpaidorder
                where partner not in ('bbseller','bbseller_snapp','bbseller_org')
                )

                UPDATE thirdparty_thpissuinginpaidorder t
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
    from thirdparty.models import ThpIssuingInPaidOrder
    from accounts.models import ProfileThpIssuingAgent

    paid_order_list =  ThpIssuingInPaidOrder.objects.all().order_by("-score")

    for item in paid_order_list:
        # print(item.score)
        work_group_needed = "fresh" if item.is_fresh else "secondary"
        right_agents = (
            ProfileThpIssuingAgent.objects
            .filter(working_insurance_company__name=item.company_name)
            .filter(Q(working_category__name=work_group_needed) | Q(working_category__name="both"))
            .filter(capacity__gt=F("assigned_order"))
            .order_by("assigned_order")
        )

        agent = right_agents.first()
        if agent is None:
            continue

        with transaction.atomic():
            item.chosen_issuing_agent = agent.person_name
            agent.assigned_order = F("assigned_order") + 1
            item.save()
            agent.save()
        
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

    await scoreing()
    await preassing()



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