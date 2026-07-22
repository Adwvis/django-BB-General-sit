from django.core.management.base import BaseCommand 
from django.utils import timezone
from pprint import pprint
from datetime import datetime
from accounts.models import ProfileThpIssuingAgent

def today():
    today_weekday = datetime.now().weekday()
    iran_weekday = (today_weekday + 2) % 7
    return iran_weekday

def test():
    # print(datetime.now())
    now_time = timezone.now().time()


    # print(iran_weekday)
    present_agents = ProfileThpIssuingAgent.objects.filter(
        start_shift__lte=now_time,
        end_shift__gte=now_time,
        is_working=True,
        is_visible=True,
        working_days__contains=[today()],
    )
    print([i.person_name for i in present_agents])

class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):

        test()


