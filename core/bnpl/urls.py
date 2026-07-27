from django.urls import path, include
from .views import BnplAccountListView , EditBnplAccount
app_name = "bnpl"

urlpatterns = [
    path("api/v1/", include("bnpl.api.v1.urls")),
    path("BnplAccountListView/",BnplAccountListView.as_view(),name="BnplAccountListView"),
    path("EditBnplAccount/<int:pk>/",EditBnplAccount.as_view(),name="EditBnplAccount"),
]