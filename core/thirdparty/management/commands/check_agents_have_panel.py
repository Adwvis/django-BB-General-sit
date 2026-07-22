
from django.core.management.base import BaseCommand , CommandError
from django.utils import timezone
import asyncio

def search_agent_in_auth_user():
    from accounts.models import ProfileThpIssuingAgent , WorkingInsuranceCompanies , AuthUserBackOffice
    
    agents_list = ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),is_working = True , is_visible= True).values("person_name","working_insurance_company__name","working_insurance_company__last_name",)

    for agent in agents_list:
        res = AuthUserBackOffice.objects.filter(first_name=agent["person_name"],last_name=agent["working_insurance_company__last_name"]).all()
        if not res.exists():
            agent_instance = ProfileThpIssuingAgent.objects.filter(person_name=agent["person_name"]).first()
            company = WorkingInsuranceCompanies.objects.filter(name=agent["working_insurance_company__name"]).first()
            if agent_instance and company:
                agent_instance.working_insurance_company.remove(company)


class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        search_agent_in_auth_user()