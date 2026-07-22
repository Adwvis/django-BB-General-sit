from django.core.management.base import BaseCommand , CommandError
from django.utils import timezone
from asgiref.sync import sync_to_async
import asyncio
import httpx
from bs4 import BeautifulSoup
from pprint import pprint


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
                from thirdparty.models import ThpIssuingOrder
                await sync_to_async(lambda: 
                    ThpIssuingOrder.objects.filter(tracking_code=item.tracking_code).update(state_name = "issuing",state_id=23))()
                
        except Exception as e:
            print(f"assing Error{e}")

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
    client.cookies.set("auth-token", bb_login_auth_token,domain="bimebazar.com")
    client.cookies.set("csrftoken", bb_login_csrftoken,domain="bimebazar.com")
    # باید سمت assing نوشته شود و موارد یه دور چک شود

    assign_list_task = [assing(item=item,client=client,semaphore=semaphore,bb_login_csrftoken=bb_login_csrftoken.token) for item in pre_assing_list]
    await asyncio.gather(*assign_list_task)

    await client.aclose()

class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        asyncio.run(assingment())





