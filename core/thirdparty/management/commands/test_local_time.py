from django.core.management.base import BaseCommand 



def now_local_time():
    from django.utils import timezone
    return timezone.localtime(timezone.now()).time()

class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        from thirdparty.models import ProfileThpIssuingAgent
        print(now_local_time())
        present_agents = ProfileThpIssuingAgent.objects.filter(
            person_name__isnull = False,
            start_shift__lte=now_local_time(),
            end_shift__gte=now_local_time(),
            is_working=True,
            is_visible=True
        ).exclude(person_name="")

        print([item.person_name for item in present_agents])