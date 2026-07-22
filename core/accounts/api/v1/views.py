from rest_framework import mixins, viewsets
from rest_framework.permissions import (IsAuthenticated,IsAuthenticatedOrReadOnly,IsAdminUser,)
from rest_framework.filters import SearchFilter, OrderingFilter
from accounts.models import ProfileThpIssuingAgent , ThpWorkingCategory , WorkingInsuranceCompanies

from .serializers import (IssuingAgentSerialazer , ThpWorkingCategorySerialazer,
 WorkingInsuranceCompaniesSerialazer, ThpIssuingPresentAgentSerialazer)

from django.utils import timezone


class ThpIssuingAgentViewSet(viewsets.ModelViewSet):
    http_method_names = ["put",'get', 'patch',]
    permission_classes = [IsAdminUser]
    serializer_class = IssuingAgentSerialazer

    def get_queryset(self):
        return ProfileThpIssuingAgent.objects.filter(is_visible=True)
    

class ThpIssuingAvailableAgentBashbordViewSet(viewsets.ModelViewSet):
    http_method_names = ['get',]
    permission_classes = [IsAdminUser]
    serializer_class = IssuingAgentSerialazer

    def get_queryset(self):
        return ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),is_working = True , is_visible= True)
    
class ThpIssuingPresentAgentBashbordViewSet(viewsets.ModelViewSet):
    http_method_names = ['get',]
    permission_classes = [IsAdminUser]
    serializer_class = ThpIssuingPresentAgentSerialazer

    def get_queryset(self):
        from datetime import datetime

        today_weekday = datetime.now().weekday()
        iran_weekday = (today_weekday + 2) % 7
        print(iran_weekday)
        return ProfileThpIssuingAgent.objects.filter(start_shift__lte=timezone.now(),end_shift__gte=timezone.now(),
                                                      working_days__contains=[iran_weekday],
                                                     is_working = True , is_visible= True)
    

class ThpWorkingCategoryViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [IsAdminUser]
    serializer_class = ThpWorkingCategorySerialazer
    def get_queryset(self):
        return ThpWorkingCategory.objects.all()
    
class WorkingInsuranceCompaniesViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [IsAdminUser]
    serializer_class = WorkingInsuranceCompaniesSerialazer
    def get_queryset(self):
        return WorkingInsuranceCompanies.objects.all()
    
# class WorkingDayViewSet(viewsets.ModelViewSet):
#     http_method_names = ['get']
#     permission_classes = [IsAdminUser]
#     serializer_class = WorkingDaySerialazer
#     def get_queryset(self):
#         return WorkingDay.objects.all()