from rest_framework import serializers

from bnpl.models import BnplAccount
from accounts.models.general import WeekDay

class BnplAccountListSerialazer(serializers.ModelSerializer):
    working_day = serializers.ListField(
        child=serializers.ChoiceField(choices=WeekDay.choices),
    )
    working_days_names = serializers.SerializerMethodField()
    class Meta:
        model = BnplAccount
        fields = [
            "id",
            "parslogic_account",
            "agent_name",
            "working_day",
            "working_days_names",
            "is_working",
        ]

    def get_working_days_names(self, obj):
        return [WeekDay(day).label for day in obj.working_day]