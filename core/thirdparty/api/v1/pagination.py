from rest_framework.pagination import PageNumberPagination

# class WorkingInsuranceCompaniesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WorkingInsuranceCompanies
#         fields = ['id', 'name']

class ThpIssuingInPaidOrderPagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100

class ThpIssuingOrderPagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100