from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from store import serializers
from store.filters import ProductFilter
from store.models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product, Review
from store.pagination import CustomPagination
from store.permissions import IsAdminOrReadOnly, ViewCustomerHistoryPermission
from store.serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CollectionSerializer, CreateOrderSerializer, CustomerSerializer, OrderSerializer, ProductSerializer, ReviewSerializer, UpdateCartItemSerializer, UpdateOrderSerializer


class ProductViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filter_class = ProductFilter
    filterset_fields = ['collection_id']
    ordering_fields = ['unit_price', 'last_update']
    pagination_class = CustomPagination
    queryset = Product.objects.all()
    search_fields = ['title', 'description', 'collection__title']
    serializer_class = ProductSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({'error': 'Cannot delete product because it is associated with an Order.'})
        return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    serializer_class = CollectionSerializer

    def get_queryset(self):
        return Collection.objects.annotate(products_count=Count('products'))


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])

    def get_serializer_context(self):
        # we get product_pk value from the url
        # /store/products/<product_pk/reviews
        # 'self.kwargs' contains URL parameters
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(
    CreateModelMixin,
    GenericViewSet,
    RetrieveModelMixin,
    DestroyModelMixin
):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs['cart_pk']).select_related('product')

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}


class CustomerViewSet(CreateModelMixin, UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    # define /store/customers/me. me is an action
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    # detail=False specifies that it is a detail view and not a list view
    def me(self, request):
        customer = Customer.objects.get(
            user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response('ok')


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'patch', 'delete', 'options', 'head', 'post']

    # overwrite method for CreateModelMixin - mixin for POST requests
    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'user_id': self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        print(order)
        # change serializer for response
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        # if user is a staff, he can view all orders
        if user.is_staff:
            return Order.objects.prefetch_related('items').all()
        # if user is logged in he can view his orders
        customer_id = Customer.objects.only(
            'id').get(user_id=user.id)
        return Order.objects.filter(customer_id=customer_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        if self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer
