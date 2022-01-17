from decimal import Decimal
from rest_framework import serializers
from .models import Collection, Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        fields=['id','title','unit_price','description','price_with_tax','collection']
        model=Product
    price_with_tax=serializers.SerializerMethodField(method_name='calc_tax_price')
    collection=serializers.HyperlinkedRelatedField(
        queryset=Collection.objects.all(),
        view_name='collections-detail'
    )

    def calc_tax_price(self,product):
        return round(product.unit_price*Decimal(1.1),2)

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        fields=['id','title','products_count']
        model=Collection
    products_count=serializers.IntegerField()