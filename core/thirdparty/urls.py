from django.urls import path, include
from .views import *
from django.views.decorators.cache import cache_page

app_name = "thirdparty"

urlpatterns = [
    path("api/v1/", include("thirdparty.api.v1.urls")),
    path("agentsList/",cache_page(10)(agentsList.as_view()),name="post-list-api"),
    path("ThpIssuingAgentsList/",cache_page(10)(ThpIssuingAgentsList.as_view()),name="ThpIssuingAgentsList"),
    # path("ThpIssuingAgentsDetail/<int:pk>/",ThpIssuingAgentsDetail.as_view(),name="ThpIssuingAgentsDetail"),
    path("EditIssuingAgent/<int:pk>/",cache_page(10)(EditIssuingAgent.as_view()),name="EditIssuingAgent"),
    path("ThpIssuingDashBoards/",cache_page(10)(ThpIssuingDashBoards.as_view()),name="ThpIssuingDashBoards"),
]
