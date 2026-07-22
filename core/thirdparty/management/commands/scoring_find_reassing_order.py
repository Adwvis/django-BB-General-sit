from django.core.management.base import BaseCommand 
from django.db import transaction
from django.db import connection


def raw_sql():
    from thirdparty.models import ThpIssuingInPaidOrder

    qs = ThpIssuingInPaidOrder.objects.raw(
            "SELECT * FROM thirdparty_thpissuinginpaidorder WHERE is_fresh = True")
    for obj in qs:
        print(obj.company_name)
        print(obj.is_fresh)

def raw_sql_cursor():

    from thirdparty.models import ThpIssuingOrder
    res = ThpIssuingOrder.objects.filter()


    with connection.cursor() as cursor:
        # cursor.execute("SELECT * FROM thirdparty_thpissuinginpaidorder WHERE is_fresh = True")
            cursor.execute("""
            WITH scoring AS (
            SELECT
                order_id,
                tracking_code,
                uid,
                state_name,
                company_name,
                exp_date,
                first_paid_date,
                sanhab_info,
                installment_type,
                partner,
                corection_loop,
                is_fresh,
                assignment_status,
            -- ========== C1: Risk Score (وزن 0.4) ==========
            (
            -- Expiration Risk (وزن 0.3)
            (CASE
                WHEN exp_date < DATE(first_paid_date) THEN 1
                WHEN exp_date = DATE(first_paid_date) THEN 0.6
                ELSE 0.2
            END) * 0.3
            +
            -- Time to SLA Breach (وزن 0.3)
            (1 - LEAST(
                CASE
                WHEN EXTRACT(HOUR FROM first_paid_date) < 21 THEN
                    EXTRACT(EPOCH FROM (DATE(first_paid_date) + INTERVAL '1 day' + TIME '21:00:00' - NOW())) / 3600
                ELSE
                    EXTRACT(EPOCH FROM (DATE(first_paid_date) + INTERVAL '2 days' + TIME '21:00:00' - NOW())) / 3600
                END / 48.0,
                1
            )) * 0.3
            +
            -- Paid Recency (وزن 0.2)
            LEAST(EXTRACT(EPOCH FROM (NOW() - first_paid_date)) / 3600 / 48.0, 1) * 0.2
            +
            -- Sanhab Status (وزن 0.1)
            case	when sanhab_info = true then 1 else 0 end * 0.1
            +
            -- Payment Type (وزن 0.1)
            (CASE installment_type
                WHEN 'cash' THEN 0.3
                WHEN 'bnpl' THEN 0.75
                WHEN 'bb_bnpl' THEN 1
                ELSE 0
            END) * 0.1
            ) AS c1_risk,

            -- ========== C2: Channel Score (وزن 0.3) ==========
            (CASE
            WHEN partner NOT IN ('autoabzar', 'snappbimeh', 'app', 'mashhad', 'tapsi') THEN
                CASE partner
                WHEN 'mashad' THEN 1
                WHEN 'snappbimeh' THEN 0.6
                WHEN 'tapsi' THEN 0.6
                ELSE 0.3
                END
            ELSE
                CASE partner
                WHEN 'mashhad' THEN 1
                WHEN 'snappbimeh' THEN 0.6
                WHEN 'tapsi' THEN 0.6
                ELSE 0.3
                END
            END) AS c2_channel,

            -- ========== C3: Process Score (وزن 0.2) ==========
            (
            -- Time Since Paid (وزن 0.4)
            LEAST(EXTRACT(EPOCH FROM (NOW() - first_paid_date)) / 3600 / 48.0, 1) * 0.4
            +
            -- Payment Time (9PM) (وزن 0.15)
            (CASE WHEN EXTRACT(HOUR FROM first_paid_date) >= 21 THEN 0 ELSE 1 END) * 0.15
            +
            -- Loop Count (وزن 0.3)
            LEAST(corection_loop / 2.0, 1) * 0.3
            ) AS c3_process,

            -- ========== C4: Type Score (وزن 0.1) ==========
            (CASE WHEN is_fresh = true THEN 1 ELSE 0 END) AS c4_type
            FROM thirdparty_thpissuingorder
            where partner not in ('bbseller','bbseller_snapp','bbseller_org')
            and state_name = 'paid')


            UPDATE thirdparty_thpissuingorder t
            SET score = ROUND(
            (0.4 * s.c1_risk + 0.3 * s.c2_channel + 0.2 * s.c3_process + 0.1 * s.c4_type)::numeric,
            4
            )
            FROM scoring s
            WHERE t.order_id = s.order_id;
                    """)
        

        # rows = cursor.fetchall()
        # print(rows)

def find_reassing_orders():
    from thirdparty.models import ThpIssuingOrder , ThpIssuingOrderLog
    from datetime import timedelta
    from django.utils import timezone

    one_hour_ago = timezone.now() - timedelta(hours=1)

    orders = ThpIssuingOrder.objects.filter(last_action__isnull=False,last_action__lt=one_hour_ago,state_name="issuing",is_issuing=True)
    data = orders.values()  # dict از همه فیلدها
    for d in data:
        # d.pop('id', None)
        d['assigned_from_id'] = d.get('chosen_issuing_agent_name_id')
        d['assignment_status'] = "preassign"
        d["chosen_issuing_agent_name_id"] = None
    new_objects = [ThpIssuingOrderLog(**d) for d in data]
    ThpIssuingOrderLog.objects.bulk_create(new_objects, batch_size=500)
    
    
    orders.update(state_name="paid",state_id=23,chosen_issuing_agent_auth_user_id=None,chosen_issuing_agent_name=None,assignment_status="preassing")



    # res = ThpIssuingOrder.objects.filter()

    print([item.tracking_code for item in orders])
    print(len(orders))

class Command(BaseCommand):
    help = "Update paid orders"

    def handle(self, *args, **options):
        # raw_sql()
        print("*"*100)
        find_reassing_orders()