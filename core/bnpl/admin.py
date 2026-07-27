from django.contrib import admin
from bnpl.models import BnplAccount
# Register your models here.
class BnplAccountAdmin(admin.ModelAdmin):
    model = BnplAccount
    list_display = ("parslogic_account", "agent_name","working_day","is_working")
    list_filter = ("working_day","is_working")
    search_fields = ("parslogic_account","agent_name","working_day","is_working")


admin.site.register(BnplAccount,BnplAccountAdmin)