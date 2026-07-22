from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
# from django.contrib.auth.forms import UserCreationForm , UserChangeForm
# from django import forms
# Register your models here.

class CustomUserAdmin(BaseUserAdmin):

    model = User
    # add_form = CustomUserCreationForm
    list_display = ("username","team","is_active","is_superuser","created_date")
    list_filter = ("team","is_active","is_superuser")
    search_fields = ("username",)
    # ordering = ("username",)

    fieldsets = (
        ("Authentication",{"fields":('username','password'),}),
        ("Permissions", {"fields": ("team","is_active","is_staff","is_superuser",)}),
        ("group permissions", {"fields": ("groups", "user_permissions",)}),
        ("Dates", {"fields": ("last_login", "created_date", "updated_date",),}),
            )
    
    readonly_fields = ("last_login","created_date", "updated_date",)

    add_fieldsets = (
        ("Authentication", {
            "classes": ("wide",),
            "fields": ("username", "password1","password2","team",),
        }),
    )

class CustomProfileThpIssuingAgentAdmin(admin.ModelAdmin):
    model = ProfileThpIssuingAgent
    list_display = ("profile_user","person_name","capacity","assigned_order","start_shift","end_shift","working_days","orders_in_issuing","is_working","is_visible")
    search_fields = ("profile_user__username","person_name")
    list_filter = ("is_working","is_visible",)

class AuthUserBackOfficeAdmin(admin.ModelAdmin):
    model = AuthUserBackOffice
    list_display = ("id","username","first_name","last_name")
    search_fields = ("id","username","first_name","last_name")

class WorkingInsuranceCompaniesAdmin(admin.ModelAdmin):
    model = AuthUserBackOffice
    list_display = ("id","name","last_name")
    search_fields = ("id","name","last_name")

class ForeignLoginTokenAdmin(admin.ModelAdmin):
    model = ForeignLoginToken
    list_display = ("name","tag","token","created_date","updated_date")
    search_fields = ("name","tag","token","created_date","updated_date")


admin.site.register(User,CustomUserAdmin)
admin.site.register(ProfileThpIssuingAgent,CustomProfileThpIssuingAgentAdmin)
admin.site.register(Team)
admin.site.register(WorkingInsuranceCompanies,WorkingInsuranceCompaniesAdmin)
admin.site.register(ThpWorkingCategory)
admin.site.register(AuthUserBackOffice,AuthUserBackOfficeAdmin)
admin.site.register(ForeignLoginToken,ForeignLoginTokenAdmin)
