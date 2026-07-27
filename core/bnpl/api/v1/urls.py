
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BnplAccountListViewSet
app_name = "bnpl-api-v1"
router_bnpl = DefaultRouter()
router_bnpl.register(
    "BnplAccountListViewSet", BnplAccountListViewSet, basename="BnplAccountListViewSet")


urlpatterns = [

]
urlpatterns += router_bnpl.urls