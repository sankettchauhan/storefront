from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view()
def product_list(request):
    return Response('ok')

@api_view()
def product_detail(request,pk):
    return Response(pk)