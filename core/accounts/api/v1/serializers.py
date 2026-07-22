from rest_framework import serializers
from accounts.models import (
ProfileThpIssuingAgent , WorkingInsuranceCompanies ,ThpWorkingCategory  ,WeekDay)
from accounts.models.general import WeekDay

class IssuingAgentSerialazer(serializers.ModelSerializer):
    profile_user = serializers.StringRelatedField()

    working_days = serializers.ListField(
        child=serializers.ChoiceField(choices=WeekDay.choices),
    )
    working_days_names = serializers.SerializerMethodField()

    working_insurance_company = serializers.PrimaryKeyRelatedField(
        many=True, queryset=WorkingInsuranceCompanies.objects.all(), write_only=True)
    working_insurance_company_names = serializers.StringRelatedField(
        source='working_insurance_company', many=True, read_only=True)

    working_category = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ThpWorkingCategory.objects.all(), write_only=True)
    working_category_names = serializers.StringRelatedField(
        source='working_category', many=True, read_only=True)

    class Meta:
        model = ProfileThpIssuingAgent
        fields = [
            "id",
            "profile_user",
            "person_name",
            "capacity",
            "assigned_order",
            "start_shift",
            "end_shift",
            "working_days",
            "working_days_names",
            "working_insurance_company",
            "working_insurance_company_names",
            "working_category",
            "working_category_names",
            "is_working",
            "is_visible",
            "orders_in_issuing",
        ]

    def get_working_days_names(self, obj):
        return [WeekDay(day).label for day in obj.working_days]


class ThpIssuingPresentAgentSerialazer(serializers.ModelSerializer):
    class Meta:
        model = ProfileThpIssuingAgent
        fields = [
            "id",
            "person_name",
            "capacity",
            "assigned_order",
        ]

class ThpWorkingCategorySerialazer(serializers.ModelSerializer):
    class Meta:
        model = ThpWorkingCategory
        fields = [
            "id",
            "name",
        ]
        
class WorkingInsuranceCompaniesSerialazer(serializers.ModelSerializer):
    class Meta:
        model = WorkingInsuranceCompanies
        fields = [
            "id",
            "name",
        ]
        
# class WorkingDaySerialazer(serializers.ModelSerializer):
#     class Meta:
#         model = WorkingDay
#         fields = [
#             "id",
#             "name",
#         ]