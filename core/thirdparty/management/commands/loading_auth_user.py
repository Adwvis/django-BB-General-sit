from django.core.management.base import BaseCommand 
from django.db import transaction

from accounts.models import AuthUserBackOffice

# import pandas as pd
import requests
import json






def MetaBaseApiCall(card_id:str):

    url = f"https://bijik.bimebazar.com/api/card/{card_id}/query/json"
    payload = json.dumps({
      "ignore_cache": True,
      "collection_preview": False,
      "parameters": []
    })
    headers = {
      'Content-Type': 'application/json',
    #   'x-api-key': 'mb_+VNkfq92qBeT2alEOed6oB0M8CrSiu8Rw=',
      'x-api-key': 'mb_+VNkfq92qBeT2alEOed6oB0M8CrSiu8Exo9Tb6mNkRw=',
      'Cookie': 'metabase.DEVICE=6fab8d2a-1169-4f5f-b67e-d94bb803c8af'
    }
    x = 0
    while True:
        try:
            return requests.request("POST", url, headers=headers, data=payload).json()
            # async with httpx.AsyncClient(timeout=120) as client:
            #     response = await client.post(url, headers=headers , data=payload)
            # return response.json()
        except Exception as e:
            print("Auth User Error: ", e)
            if x >= 5:
                return None


class Command(BaseCommand):
    help = "Import Auth User data"

    def handle(self, *args, **options):
        auth_user_data = MetaBaseApiCall("13472")
        if auth_user_data == None:
            self.stdout.write(self.style.WARNING(f'We tryed 5 time but MetaBase Didnt responed'))
            return
        
        AuthUserBackOffice.objects.all().delete()

        # records = auth_user_data.to_dict('records')
        objects = [AuthUserBackOffice(**record) for record in auth_user_data]
        AuthUserBackOffice.objects.bulk_create(objects, batch_size=1000)
        
        self.stdout.write(self.style.SUCCESS(f'{len(objects)} New recorders Added '))
