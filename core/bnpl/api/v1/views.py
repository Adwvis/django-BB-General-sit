from rest_framework import mixins, viewsets
from rest_framework.permissions import (IsAuthenticated,IsAuthenticatedOrReadOnly,IsAdminUser,)
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from bnpl.models import BnplAccount
from .serializers import BnplAccountListSerialazer

class BnplAccountListViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    serializer_class = BnplAccountListSerialazer
    def get_queryset(self):
        return BnplAccount.objects.all()