from decimal import Decimal
import functools
from rest_framework import serializers
from .models import Cart, CartItem, Collection, Customer, Order, Product, Review


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'title', 'unit_price',
                  'description', 'price_with_tax', 'collection']
        model = Product
    price_with_tax = serializers.SerializerMethodField(
        method_name='calc_tax_price')
    # collection=serializers.HyperlinkedRelatedField(
    #     queryset=Collection.objects.all(),
    #     view_name='collections-detail'
    # )

    def calc_tax_price(self, product):
        return round(product.unit_price*Decimal(1.1), 2)


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'title', 'products_count']
        model = Collection
    products_count = serializers.IntegerField()


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'description', 'date']
        model = Review

    def create(self, validated_data):
        product_id = self.context['product_id']
        # '**validated_data' unpacks the existing data
        return Review.objects.create(product_id=product_id, **validated_data)


class CartItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class CartItemSerializer(serializers.ModelSerializer):
    product = CartItemProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

    def get_total_price(self, item):
        return item.quantity*item.product.unit_price


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        return sum(c.quantity*c.product.unit_price for c in cart.items.all())

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']

    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(product_id=self.request['product_id']).exists():
            raise serializers.ValidationError('No product found for given id.')
        return value

    def save(self, **kwargs):
        # from request
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        # from URL
        cart_id = self.context['cart_id']
        try:
            # if product in cart exists then increase quantity
            cart_item = CartItem.objects.get(
                cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            self.instance = cart_item.save()
        except CartItem.DoesNotExist:
            # else create new cart item
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data)
        return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'customer', 'payment_status', 'placed_at']
