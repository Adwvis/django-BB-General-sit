from django.db import models

from accounts.models import ProfileThpIssuingAgent
# Create your models here.

class ThpIssuingInPaidOrder(models.Model):

    # sanhab_info = True/False (if any field of sanhab had value = True)
    # corection_loop = loop of order
    order_id = models.IntegerField()
    tracking_code = models.IntegerField(primary_key=True,unique=True)
    uid = models.CharField(max_length=255)

    state_id = models.CharField(max_length=255)
    state_name = models.CharField(max_length=255)

    company_id = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)

    issuing_agent_id = models.IntegerField(blank=True,null=True)
    # issuing_agent_name = models.CharField(max_length=255)
    chosen_issuing_agent_auth_user_id = models.IntegerField(blank=True,null=True)
    # chosen_issuing_agent = models.ForeignKey(ProfileThpIssuingAgent, on_delete=models.SET_NULL,null=True,blank=True)
    chosen_issuing_agent = models.CharField(max_length=255,blank=True,null=True)

    exp_date = models.DateField(blank=True,null=True)
    first_paid_date = models.DateTimeField(blank=True,null=True)
    
    sanhab_info = models.BooleanField(blank=True,null=True)
    installment_type = models.CharField(max_length=100,blank=True,null=True)
    
    partner = models.CharField(max_length=100,blank=True,null=True)
    corection_loop = models.IntegerField(blank=True,null=True)
    
    is_fresh = models.BooleanField(blank=True,null=True)
    score = models.FloatField(null=True,blank=True)
    assignment_status = models.CharField(max_length=100,choices=[
        ("pending", "pending"),("assigned", "assigned"),("preassigned", "preassigned"),("returned","returned")],default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.tracking_code)

class ThpIssuingInIssuingOrder(models.Model):

    order_id = models.IntegerField()
    tracking_code = models.IntegerField(primary_key=True,unique=True)
    uid = models.CharField(max_length=255)

    state_id = models.CharField(max_length=255)
    state_name = models.CharField(max_length=255)

    company_id = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)

    issuing_agent_id = models.IntegerField(blank=True,null=True)
    issuing_agent_name = models.CharField(max_length=255,blank=True,null=True)

    is_issuing = models.BooleanField(blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ThpIssuingOrderLog(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.IntegerField(blank=True,null=True)
    tracking_code = models.IntegerField(blank=True,null=True)
    uid = models.CharField(max_length=255,blank=True,null=True)

    assigned_from = models.ForeignKey(ProfileThpIssuingAgent,related_name="assigned_from", on_delete=models.DO_NOTHING,null=True,blank=True)

    state_id = models.CharField(max_length=255,blank=True,null=True)
    state_name = models.CharField(max_length=255,blank=True,null=True)

    company_id = models.CharField(max_length=100,blank=True,null=True)
    company_name = models.CharField(max_length=100,blank=True,null=True)

    issuing_agent_id = models.IntegerField(blank=True,null=True)
    chosen_issuing_agent_auth_user_id = models.IntegerField(blank=True,null=True)
    chosen_issuing_agent_name = models.ForeignKey(ProfileThpIssuingAgent,related_name="chosen_issuing_agent_name", on_delete=models.DO_NOTHING,null=True,blank=True)


    exp_date = models.DateField(blank=True,null=True)
    first_paid_date = models.DateTimeField(blank=True,null=True)
    
    sanhab_info = models.BooleanField(blank=True,null=True)
    installment_type = models.CharField(max_length=100,blank=True,null=True)
    
    partner = models.CharField(max_length=100,blank=True,null=True)
    corection_loop = models.IntegerField(blank=True,null=True)
    
    is_fresh = models.BooleanField(blank=True,null=True)
    score = models.IntegerField(null=True,blank=True)

    is_issuing = models.BooleanField(blank=True,null=True)
    last_action = models.DateTimeField(blank=True,null=True)

    assignment_status = models.CharField(max_length=100,choices=[("reassigned","reassigned"),],default=None,null=True,blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.tracking_code)


# class ThpIssuingOrderLog



class ThpIssuingOrder(models.Model):
    
    order_id = models.IntegerField()
    tracking_code = models.IntegerField(primary_key=True,unique=True)
    uid = models.CharField(max_length=255)

    state_id = models.CharField(max_length=255)
    state_name = models.CharField(max_length=255)

    company_id = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)

    issuing_agent_id = models.IntegerField(blank=True,null=True)
    # issuing_agent_name = models.CharField(max_length=255)
    chosen_issuing_agent_auth_user_id = models.IntegerField(blank=True,null=True)
    chosen_issuing_agent_name = models.ForeignKey(ProfileThpIssuingAgent, on_delete=models.SET_NULL,null=True,blank=True)
    # chosen_issuing_agent_name = models.CharField(max_length=255,blank=True,null=True)

    exp_date = models.DateField(blank=True,null=True)
    first_paid_date = models.DateTimeField(blank=True,null=True)
    
    sanhab_info = models.BooleanField(blank=True,null=True)
    installment_type = models.CharField(max_length=100,blank=True,null=True)
    
    partner = models.CharField(max_length=100,blank=True,null=True)
    corection_loop = models.IntegerField(blank=True,null=True)
    
    is_fresh = models.BooleanField(blank=True,null=True)
    score = models.FloatField(null=True,blank=True)

    is_issuing = models.BooleanField(blank=True,null=True)

    assignment_status = models.CharField(max_length=100,choices=[("reassigned","reassigned"),],default=None,null=True,blank=True)

    last_action = models.DateTimeField(blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return str(self.tracking_code)
    
