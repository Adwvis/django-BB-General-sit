from django.db import models
from accounts.models.general import WeekDay
from django.contrib.postgres.fields import ArrayField
# Create your models here.



class BnplAccount(models.Model):
    parslogic_account = models.CharField(unique=True)
    agent_name = models.CharField(blank=True,null=True,unique=True)
    working_day = ArrayField(models.IntegerField(choices=WeekDay.choices),blank=True,default=list,)
    is_working = models.BooleanField(default=True)
    def __str__(self):
        return self.parslogic_account

