from django.core.management.base import BaseCommand
from django.db.models import Subquery, OuterRef


def specify_issuing_agent_name():
    help = "This def is for updateing names in ThpIssuingInIssuingOrder table (joins issuing_agent_id to AuthUser tables and write it on ThpIssuingInIssuingOrder)"

    from accounts.models import AuthUserBackOffice , ProfileThpIssuingAgent
    from thirdparty.models import ThpIssuingOrder
    from django.db.models import Value
    from django.db.models.functions import Concat

    # ThpIssuingOrder.objects.update(
    # issuing_agent_name=Subquery(
    #     ProfileThpIssuingAgent.objects.filter(AuthUserBackOffice.objects.filter(
    #         id=OuterRef("issuing_agent_id")
    #     ).values("first_name")[:1])))
    
 
    from django.db.models import Value
    from django.db.models.functions import Concat

    ThpIssuingOrder.objects.filter(issuing_agent_id__isnull=False).update(
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
    # user_first_name = AuthUserBackOffice.objects.filter(
    # id=OuterRef("issuing_agent_id")
    # ).values("first_name")[:1]

    # profile = ProfileThpIssuingAgent.objects.filter(
    #     person_name=Subquery(user_first_name)
    # ).values("pk")[:1]

    # ThpIssuingOrder.objects.update(
    #     chosen_issuing_agent_name=Subquery(profile)
    # )

    # ThpIssuingInIssuingOrder.objects.update(
    # issuing_agent_name=Subquery(
    #     AuthUserBackOffice.objects.filter(
    #         id=OuterRef("issuing_agent_id")
    #     ).values("first_name")[:1]))
    
    # UPDATE issuing_list
    #     SET agent_name = (
    #         SELECT first_name
    #         FROM auth_user
    #         WHERE auth_user.id = issuing_list.agent_id
    #         LIMIT 1
    #     );


class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        specify_issuing_agent_name()