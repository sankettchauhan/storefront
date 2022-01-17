from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from store.filters import ProductFilter
from store.models import Collection, OrderItem, Product, Review
from store.serializers import CollectionSerializer, ProductSerializer, ReviewSerializer

class ProductViewSet(ModelViewSet):
    filter_backends=[DjangoFilterBackend]
    filter_class=ProductFilter
    filterset_fields=['collection_id']
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

class ReviewViewSet(ModelViewSet):
    serializer_class=ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        # we get product_pk value from the url
        # /store/products/<product_pk/reviews
        # 'self.kwargs' contains URL parameters
        return {'product_id':self.kwargs['product_pk']}