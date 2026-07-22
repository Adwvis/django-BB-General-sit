
from django.urls import path, include
from .views import ThpIssuingInPaidOrderViewSet  , ThpIssuingInPaidOrderBashbordViewSet ,ThpIssuingBashbordTextViewSet , ThpIssuingOrderViewSet
from rest_framework.routers import DefaultRouter

router_thirdparty = DefaultRouter()
router_thirdparty.register(
    "ThpIssuingInPaidOrder", ThpIssuingInPaidOrderViewSet, basename="ThpIssuingInPaidOrder"
)
# router_thirdparty.register(
#     "ThpIssuingOrderLog", ThpIssuingOrderLogViewSet, basename="ThpIssuingOrderLogViewSet"
# )
router_thirdparty.register(
    "ThpIssuingInPaidOrderBashbord", ThpIssuingInPaidOrderBashbordViewSet, basename="ThpIssuingInPaidOrderBashbordViewSet"
)
router_thirdparty.register(
    "ThpIssuingBashbordText", ThpIssuingBashbordTextViewSet, basename="ThpIssuingBashbordTextViewSet"
)
router_thirdparty.register(
    "ThpIssuThpIssuingOrder", ThpIssuingOrderViewSet, basename="ThpIssuingOrderViewSet"
)

app_name = "thirdparty-api-v1"

urlpatterns = [

]
urlpatterns += router_thirdparty.urls
