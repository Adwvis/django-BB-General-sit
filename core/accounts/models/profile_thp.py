from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
# from accounts.models import WeekDay
from accounts.models.general import WeekDay

class ProfileThpIssuingAgent(models.Model):

    profile_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    person_name = models.CharField(max_length=255,blank=True)

    capacity = models.IntegerField(default=0)
    assigned_order = models.IntegerField(default=0)
    
    start_shift = models.TimeField(default="00:00:00")
    end_shift = models.TimeField(default="00:00:00")

    # working_days = models.ManyToManyField("WorkingDay", blank=True)
    working_days = ArrayField(
        models.IntegerField(choices=WeekDay.choices),
        blank=True,
        default=list,
    )
    working_insurance_company = models.ManyToManyField("WorkingInsuranceCompanies", blank=True)
    working_category = models.ManyToManyField("ThpWorkingCategory", blank=True)

    orders_in_issuing = models.TextField(max_length=512,blank=True,null=True)

    is_working = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return self.person_name if self.person_name else str(self.profile_user)
    


    
class ThpWorkingCategory(models.Model):
    name = models.CharField(max_length=250,unique=True)

    def __str__(self):
        return self.name
    

