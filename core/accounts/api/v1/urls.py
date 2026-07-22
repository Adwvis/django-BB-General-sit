
from django.urls import path, include
from .views import (ThpIssuingAgentViewSet , ThpWorkingCategoryViewSet , WorkingInsuranceCompaniesViewSet ,
                     ThpIssuingAvailableAgentBashbordViewSet, ThpIssuingPresentAgentBashbordViewSet)
from rest_framework.routers import DefaultRouter

router_accounts = DefaultRouter()
router_accounts.register(
    "ThpIssuingAgent", ThpIssuingAgentViewSet, basename="ThpIssuingAgent")
router_accounts.register(
    "ThpWorkingCategory", ThpWorkingCategoryViewSet, basename="ThpWorkingCategoryViewSet")
router_accounts.register(
    "WorkingInsuranceCompanies", WorkingInsuranceCompaniesViewSet, basename="WorkingInsuranceCompaniesViewSet")
# router_accounts.register(
#     "WorkingDay", WorkingDayViewSet, basename="WorkingDayViewSet")
router_accounts.register(
    "ThpIssuingAvailableAgentBashbord", ThpIssuingAvailableAgentBashbordViewSet, basename="ThpIssuingAvailableAgentBashbord")
router_accounts.register(
    "ThpIssuingPresentAgentBashbordViewSet", ThpIssuingPresentAgentBashbordViewSet, basename="ThpIssuingPresentAgentBashbordViewSet")

app_name = "accounts-api-v1"

urlpatterns = [

]
urlpatterns += router_accounts.urls
