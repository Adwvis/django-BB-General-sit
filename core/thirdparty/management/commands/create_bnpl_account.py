from django.core.management.base import BaseCommand
from bnpl.models import BnplAccount

class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):


        for i in range(2, 31):
            BnplAccount.objects.create(
                parslogic_account=f"account {i}",
                agent_name="",
                working_day="0,1,2,3,4,5",
                is_working = True
            )

        self.stdout.write(
            self.style.SUCCESS("account created successfully.")
        )

        self.stdout.write(self.style.SUCCESS("Done."))