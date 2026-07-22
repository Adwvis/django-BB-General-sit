
from django.core.management.base import BaseCommand 



def test():
    from thirdparty.models import ThpIssuingOrder
    data = ThpIssuingOrder.objects.filter(state_name = "paid",chosen_issuing_agent_name__isnull=False)
    print([(item.chosen_issuing_agent_name,item.tracking_code) for item in data])
    data = ThpIssuingOrder.objects.filter(state_name = "paid",chosen_issuing_agent_name__isnull=False).update(chosen_issuing_agent_name=None)


class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        test()