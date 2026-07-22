from django.urls import path, include
from .views import HomeView
app_name = "accounts"

urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("api/v1/", include("accounts.api.v1.urls")),
    path("UrlsMap/", HomeView.as_view(), name="UrlsMap"),
]