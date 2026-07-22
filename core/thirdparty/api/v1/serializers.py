from rest_framework import serializers
from ...models import ThpIssuingInPaidOrder , ThpIssuingOrderLog , ThpIssuingOrder
from accounts.models import ProfileThpIssuingAgent


# class WorkingInsuranceCompaniesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WorkingInsuranceCompanies
#         fields = ['id', 'name']



class ThpIssuingInPaidOrderSerialazer(serializers.ModelSerializer):
    # chosen_issuing_agent = serializers.StringRelatedField(source='chosen_issuing_agent.profile_user')
    chosen_issuing_agent= serializers.StringRelatedField()
    class Meta:
        model = ThpIssuingInPaidOrder
        fields = [
            "tracking_code",
            "order_id",
            "uid",
            "company_name",
            "state_name",
            "score",
            "chosen_issuing_agent",
            "assignment_status",
        ]
        
class ThpIssuingOrderSerialazer(serializers.ModelSerializer):
    chosen_issuing_agent_name= serializers.StringRelatedField()
    class Meta:
        model = ThpIssuingOrder
        fields = [
            "tracking_code",
            "order_id",
            "uid",
            "state_id",
            "state_name",
            "company_id",
            "company_name",
            "issuing_agent_id",
            "chosen_issuing_agent_auth_user_id",
            "chosen_issuing_agent_name",
            "exp_date",
            "first_paid_date",
            "sanhab_info",
            "installment_type",
            "partner",
            "corection_loop",
            "is_fresh",
            "score",
            "is_issuing",
            "assignment_status",
            "created_at",
            "updated_at",
        ]

class ThpIssuingInPaidOrderBashbordSerialazer(serializers.Serializer):
    # chosen_issuing_agent = serializers.StringRelatedField(source='chosen_issuing_agent.profile_user')
    company_name = serializers.CharField()
    order_count = serializers.IntegerField()
    fresh = serializers.IntegerField()
    secondry = serializers.IntegerField()


class ThpIssuingBashbordTextSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    person_name = serializers.CharField()
    total_assign_count = serializers.IntegerField()
    # capacity = serializers.IntegerField()
    reassign_count = serializers.IntegerField()
    orders_in_issuing = serializers.JSONField()



class ThpIssuingOrderLogSerialazer(serializers.ModelSerializer):
    class Meta:
        model = ThpIssuingOrderLog
        fields = [
            "tracking_code",
            "assigned_from",
            "assigned_to",
            "created_at",
        ]