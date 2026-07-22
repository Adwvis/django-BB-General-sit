from django.core.management.base import BaseCommand 
from django.forms.models import model_to_dict


def create():
    from thirdparty.models import ThpIssuingOrder , ThpIssuingOrderLog

    item = ThpIssuingOrder.objects.first()
    print(item.tracking_code)
    data = model_to_dict(item)
    print(data)
    data['assignment_status'] = "assigned"
    data["chosen_issuing_agent_name_id"] = data.pop("chosen_issuing_agent_name")
    ThpIssuingOrderLog.objects.create(**data)

class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        # raw_sql()
        print("*"*100)
        create()

