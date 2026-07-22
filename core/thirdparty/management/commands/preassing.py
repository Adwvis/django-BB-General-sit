from django.core.management.base import BaseCommand 
from django.db import transaction
from django.db import connection
from django.db.models import OuterRef, Subquery , Q , Count, CharField , Aggregate , F

def get_reassign_orders():
    from thirdparty.models import ThpIssuingOrderLog
    from accounts.models import ProfileThpIssuingAgent

    agent_id = ThpIssuingOrderLog.objects.filter(tracking_code="9708222",assignment_status="reassigned").values("assigned_from_id")
    # agent = ThpIssuingOrderLog.objects.filter(tracking_code="9708222",assignment_status="reassigned").va

    print(agent_id)
    
    check = ProfileThpIssuingAgent.objects.exclude(id__in=agent_id)
    print(check.values())
    print(len(check))



class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        get_reassign_orders()




