from django.contrib import admin

# Register your models here.
from .models import *


class ThpIssuingInPaidOrderAdmin(admin.ModelAdmin):
    model = ThpIssuingInPaidOrder
    list_display = ("tracking_code","company_name","partner","is_fresh","chosen_issuing_agent","score")
    list_filter = ("is_fresh","assignment_status",)
    search_fields = ("tracking_code","order_id","uid","company_name")
    ordering = ["-score"]

class ThpIssuingInIssuingOrderAdmin(admin.ModelAdmin):
    model = ThpIssuingInIssuingOrder
    list_display = ("tracking_code","company_name","issuing_agent_id","issuing_agent_name","is_issuing")
    list_filter = ("is_issuing",)
    search_fields = ("tracking_code","order_id","uid","issuing_agent_name")

class CustomIssuingOrderLogAdmin(admin.ModelAdmin):
    model = ThpIssuingOrderLog
    list_display = ("tracking_code","assigned_from","chosen_issuing_agent_name","assignment_status","created_at")
    list_filter = ("is_issuing","state_name","is_issuing","assignment_status")
    search_fields = ("tracking_code","order_id","uid","chosen_issuing_agent_name__person_name",
                     "assigned_from__person_name","assignment_status","assignment_status")

    readonly_fields = ("created_at",)

class ThpissuingOrderAdmin(admin.ModelAdmin):
    model = ThpIssuingOrder
    list_display = ("tracking_code","company_name","state_name","issuing_agent_id","first_paid_date",
                    "is_issuing","chosen_issuing_agent_auth_user_id","chosen_issuing_agent_name","score",
                    "assignment_status")
    list_filter = ("is_issuing","state_name","is_issuing","assignment_status")
    search_fields = ("tracking_code","order_id","uid","chosen_issuing_agent_name__person_name",)


admin.site.register(ThpIssuingInPaidOrder,ThpIssuingInPaidOrderAdmin)
admin.site.register(ThpIssuingInIssuingOrder,ThpIssuingInIssuingOrderAdmin)
admin.site.register(ThpIssuingOrderLog,CustomIssuingOrderLogAdmin)
admin.site.register(ThpIssuingOrder,ThpissuingOrderAdmin)