from django.db import models


# class WorkingDay(models.Model):
#     name = models.CharField(max_length=250)

#     def __str__(self):
#         return self.name

class WeekDay(models.IntegerChoices):
    SATURDAY = 0, "شنبه"
    SUNDAY = 1, "یکشنبه"
    MONDAY = 2, "دوشنبه"
    TUESDAY = 3, "سه‌شنبه"
    WEDNESDAY = 4, "چهارشنبه"
    THURSDAY = 5, "پنج‌شنبه"
    FRIDAY = 6, "جمعه"

class WorkingInsuranceCompanies(models.Model):
    name = models.CharField(max_length=250,unique=True)
    last_name = models.CharField(max_length=250)

    def __str__(self):
        return self.name
    

class AuthUserBackOffice(models.Model):
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.username
    

class ForeignLoginToken(models.Model):
    name = models.CharField(unique=True)
    tag = models.CharField(blank=True,null=True)
    token = models.CharField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name