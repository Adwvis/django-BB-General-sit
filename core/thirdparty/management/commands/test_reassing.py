from django.core.management.base import BaseCommand 
from asgiref.sync import sync_to_async
from django.db import transaction , connection
import asyncio
import httpx

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


async def chang_state_in_back_office_to_paid(item,client,semaphore,bb_login_csrftoken):
    async with semaphore:
        try:
            print("start chang_state_in_back_office_to_paid")
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
            print(f"response_change_state , {response_change_state.status_code},{response_change_state.text}")
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



class Command(BaseCommand):
    help = "Update paid orders"

    asyncio.run(find_reassine())

