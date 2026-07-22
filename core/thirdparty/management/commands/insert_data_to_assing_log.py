from django.core.management.base import BaseCommand
from django.utils import timezone
from thirdparty.models import ThpIssuingOrderLog
import random, datetime

COMPANIES = [("sina","sina"), ("saman","saman"), ("ma","ma"), ("razi","razi"), ("tavon","tavon")]
STATES = [("10","10"), ("20","20"), ("30","30")]
AGENTS = ["سمیه قراگوزلو", "محیا صمدی", "امیرمهدی قاسمیان","ساناز شمس","مینا ملکی","سجاد کوهی گونیانی","دلنیا کوکه ای","مریم خوش گرد","علی دارینی","رضا سیر"]

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        objs = []
        for i in range(200):
            cid, cname = random.choice(COMPANIES)
            sid, sname = random.choice(STATES)
            objs.append(ThpIssuingOrderLog(
                order_id=1000+i,
                tracking_code=5000+i,
                uid=f"uid-{i}",
                # assigned_from=random.choice(AGENTS),
                assigned_to=random.choice(AGENTS),
                state_id=sid, state_name=sname,
                company_id=cid, company_name=cname,
                issuing_agent_id=random.randint(1,10),
                chosen_issuing_agent=random.choice(AGENTS),
                exp_date=datetime.date.today() + datetime.timedelta(days=random.randint(30,365)),
                first_paid_date=timezone.now() - datetime.timedelta(days=random.randint(0,180)),
                sanhab_info=random.choice([True, False]),
                installment_type=random.choice(["monthly","quarterly","yearly"]),
                partner=random.choice(["partner_a","partner_b",None]),
                corection_loop=random.randint(0,5),
                is_fresh=random.choice([True, False]),
                score=random.choice([None, random.randint(1,100)]),
                assignment_status=random.choice(["pending","assigned","preassigned","returned"]),
            ))
        ThpIssuingOrderLog.objects.bulk_create(objs)
        self.stdout.write(f"{len(objs)} records created.")