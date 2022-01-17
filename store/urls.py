from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

router=routers.DefaultRouter()
router.register('products',views.ProductViewSet,basename='products')
router.register('collections',views.CollectionViewSet,basename='collections')

products_router=routers.NestedDefaultRouter(
    router,'products',
    # lookup attribute specifies the variable name
    lookup='product'
    # value is saved in a variable named 'product_pk'
    # /store/products/<product_pk>/reviews/
)
products_router.register('reviews',views.ReviewViewSet,basename='product-reviews')

urlpatterns=router.urls+products_router.urls