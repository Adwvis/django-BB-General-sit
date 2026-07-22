from django.core.management.base import BaseCommand , CommandError
from django.db.models import Count, CharField , Aggregate


class GroupConcat(Aggregate):
    function = "GROUP_CONCAT"
    template = "%(function)s(%(expressions)s, '%(separator)s')"
    output_field = CharField()

    def __init__(self, expression, separator=", ", **extra):
        super().__init__(expression, separator=separator, **extra)


def agents_issuing_counts():
    from thirdparty.models import ThpIssuingInIssuingOrder
    from accounts.models import ProfileThpIssuingAgent
    result = (
        ThpIssuingInIssuingOrder.objects
        .filter(is_issuing=True)
        .values("issuing_agent_name")
        .annotate(
            count_=Count("tracking_code"),
            companies=GroupConcat("company_name"),
            tracking_codes=GroupConcat("tracking_code"),
        )
        .order_by("issuing_agent_name")
    )

    for item in result:
        print(item)
        agent_instance = ProfileThpIssuingAgent.objects.filter(person_name=item["issuing_agent_name"]).first()

        agent_instance.orders_in_issuing = (item["companies"] + " - " + item["tracking_codes"])
        agent_instance.assigned_order = (item["count_"])
        agent_instance.save()



    


class Command(BaseCommand):
    help = "agents_issuing_counts and updating"

    def handle(self, *args, **options):
        agents_issuing_counts()