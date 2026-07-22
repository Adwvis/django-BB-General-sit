from rest_framework import mixins, viewsets
from rest_framework.permissions import (IsAuthenticated,IsAuthenticatedOrReadOnly,IsAdminUser,)
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from ...models import ThpIssuingInPaidOrder , ThpIssuingOrderLog , ThpIssuingOrder 
from .serializers import ThpIssuingInPaidOrderSerialazer , ThpIssuingOrderLogSerialazer , ThpIssuingInPaidOrderBashbordSerialazer , ThpIssuingBashbordTextSerializer , ThpIssuingOrderSerialazer
from .pagination import ThpIssuingInPaidOrderPagination , ThpIssuingOrderPagination


class ThpIssuingInPaidOrderViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [IsAdminUser]
    serializer_class = ThpIssuingInPaidOrderSerialazer
    pagination_class = ThpIssuingInPaidOrderPagination
    def get_queryset(self):
        return ThpIssuingInPaidOrder.objects.all()
    
class ThpIssuingOrderViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [IsAdminUser]
    serializer_class = ThpIssuingOrderSerialazer
    pagination_class = ThpIssuingOrderPagination
    def get_queryset(self):
        return ThpIssuingOrder.objects.all()
    

class ThpIssuingInPaidOrderBashbordViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [IsAdminUser]
    serializer_class = ThpIssuingInPaidOrderBashbordSerialazer
    # pagination_class = ThpIssuingInPaidOrderPagination
    def get_queryset(self):
        from django.db.models import Count, Sum, Case, When, IntegerField, Q

        return (ThpIssuingOrder.objects
                .filter(score__isnull=False,state_name = "paid")
                .values('company_name')
                .annotate(
                    order_count=Count('tracking_code'),
                    fresh=Sum(Case(When(is_fresh=True, then=1), default=0, output_field=IntegerField())),
                    secondry=Sum(Case(When(is_fresh=False, then=1), default=0, output_field=IntegerField())),
                )
            )
    
class ThpIssuingBashbordTextViewSet(viewsets.ViewSet):
    http_method_names = ["get"]
    permission_classes = [IsAdminUser]

    def list(self, request):
        from django.db import connection
        query = """
            WITH total_assign_count AS (
            SELECT
                chosen_issuing_agent_name_id,
                COUNT(tracking_code) AS total_assign_count
            FROM public.thirdparty_thpissuingorderlog
            where chosen_issuing_agent_name_id is not null
            GROUP BY chosen_issuing_agent_name_id
            ),
            reassign_count AS (
            SELECT
                assigned_from_id,
                COUNT(tracking_code) AS reassign_count
            FROM public.thirdparty_thpissuingorderlog
            WHERE assigned_from_id IS NOT NULL
            GROUP BY assigned_from_id
            )

            SELECT
                p.id,
                p.person_name,
                COALESCE(t.total_assign_count, 0) AS total_assign_count,
                COALESCE(r.reassign_count, 0) AS reassign_count,
                p.orders_in_issuing
            FROM total_assign_count t
            LEFT JOIN reassign_count r
                ON t.chosen_issuing_agent_name_id = r.assigned_from_id
            LEFT JOIN accounts_profilethpissuingagent p
                ON p.id = t.chosen_issuing_agent_name_id
            WHERE p.is_working = true
            AND p.is_visible = true;
        """

        with connection.cursor() as cursor:
            cursor.execute(query)

            columns = [col[0] for col in cursor.description]
            rows = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        serializer = ThpIssuingBashbordTextSerializer(rows, many=True)
        return Response(serializer.data)