from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,AbstractBaseUser,PermissionsMixin,)
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserManager(BaseUserManager):

    def create_user(self,username ,password,**extra_fields):
        if not username :
            raise ValueError(_("username must be set"))
        user = self.model(username=username ,**extra_fields)
        user.set_password(password)
        user.save()
        return user 

    def create_superuser(self,username ,password,**extra_fields):
        
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_active',True)
        extra_fields.setdefault('is_superuser',True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_("SuperUser is staff"))
        if extra_fields.get('is_active') is not True:
            raise ValueError(_("SuperUser is active"))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_("SuperUser is superuser"))
        return self.create_user(username ,password,**extra_fields)

class User(AbstractBaseUser,PermissionsMixin):
    username = models.CharField(max_length=255,unique=True)

    
    is_active =models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    team = models.ForeignKey("Team",on_delete=models.SET_NULL,null=True)

    # is_verified = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    

    # first_name = models.CharField(max_length=20)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username 

class Team(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name
    


@receiver(post_save, sender=User)
def save_profile(sender, instance, created, **kwargs):

    if not created:
        return
    
    if instance.team:
        from .profile_thp import ProfileThpIssuingAgent
        if instance.team.name == "ThpIssunigAgent":
            ProfileThpIssuingAgent.objects.create(profile_user=instance,)