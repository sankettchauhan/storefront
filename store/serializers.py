from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from .models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product, Review


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


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
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
        # if not Product.objects.filter(product_id=self.request['product_id']).exists():
        if not Product.objects.filter(id=value).exists():
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


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'unit_price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'items', 'payment_status', 'placed_at']


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart found.')
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('Cart is empty.')

    def save(self, **kwargs):
        cart_id = self.validated_data['cart_id']
        (customer, created) = Customer.objects\
            .get_or_create(user_id=self.context['user_id'])
        # to create an order we only require customer
        order = Order.objects.create(customer=customer)
        cart_items = CartItem.objects.filter(cart_id=cart_id)
        # print('cart items: ', cart_items)
        # ṭo create order items we need order object of the customer and
        # the cart from which items need to be transferred from cart to order table
        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.unit_price
            ) for item in cart_items
        ]
        # print('order items: ', order_items)
        OrderItem.objects.bulk_create(order_items)
        # Cart.objects.filter(pk=cart_id).delete()
        return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model=Order
        fields=['payment_status']