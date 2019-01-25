from django.shortcuts import render

# Create your views here.
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView

from goods.models import SKU
from goods.serializers import SKUSerializer


# GET /categories/(?P<category_id>\d+)/skus?page=xxx&page_size=xxx&ordering=xxx
class SKUListView(ListAPIView):

    serializer_class = SKUSerializer

    # ordering
    filter_backends = (OrderingFilter,)
    ordering_fields = ('create_time', 'price', 'sales')

    # pagination: global setting in dev.py

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id, is_launched=True)

