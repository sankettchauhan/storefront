from django.db.models import Count
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from store.models import Collection, OrderItem, Product
from store.serializers import CollectionSerializer, ProductSerializer

class ProductViewSet(ModelViewSet):
    queryset=Product.objects.all()
    serializer_class=ProductSerializer

    def get_serializer_context(self):
        return {'request':self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count()>0:
            return Response({'error':'Cannot delete product because it is associated with an Order.'})
        return super().destroy(request, *args, **kwargs)

class CollectionViewSet(ModelViewSet):
    serializer_class=CollectionSerializer

    def get_queryset(self):
        return Collection.objects.annotate(products_count=Count('products'))