from django.db.models import Prefetch
from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from products.models import ProductType, Product, ProductVariant, Order, OrderHistory
from products.serializers import (
    CreateOrderSerializer,
    OrderListSerializer,
    ProductTypesSerializer,
    ProductsListSerializer,
    ProductVariantsListSerializer,
    ProductInfoSerializer,
    ProductVariantInfoSerializer,
    OrdersSerializer,
)
from products.services import get_or_create_customer, process_order_request
from vanguard.permissions import IsDeveloperUser, IsAdminUser, IsStaffUser


class ProductTypesViewSet(ModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypesSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        queryset = ProductType.objects.all().order_by("type")

        return queryset


class ProductVariantsListViewSet(ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantsListSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        variant_id = self.request.query_params.get("variant_id", None)
        sku = self.request.query_params.get("sku", None)

        queryset = ProductVariant.objects.all().order_by("product")
        if variant_id:
            queryset = queryset.filter(variant_id=variant_id)

        if sku:
            queryset = queryset.filter(sku=sku)

        return queryset


class ProductsListViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductsListSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        product_id = self.request.query_params.get("product_id", None)

        queryset = Product.objects.all().order_by("product_type")
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset


class ProductInfoViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductInfoSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        product_id = self.request.query_params.get("product_id", None)
        if product_id:
            queryset = Product.objects.exclude(is_deleted=True).filter(product_id=product_id)

            return queryset


class ProductVariantInfoViewSet(ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantInfoSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        sku = self.request.query_params.get("sku", None)
        if sku:
            queryset = ProductVariant.objects.exclude(is_deleted=True).filter(sku=sku)

            return queryset


class OrdersViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrdersSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        order_id = self.request.query_params.get("order_id", None)

        queryset = Order.objects.prefetch_related(
            Prefetch("histories", queryset=OrderHistory.objects.order_by("-id"))
        ).all()
        if order_id:
            queryset = queryset.filter(id=order_id.lstrip("0"))

        return queryset


class OrdersListViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]
    http_method_names = ["get"]

    def get_queryset(self):
        return Order.objects.all().order_by("-id")


# POST Views
class CreateOrderView(views.APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        customer = get_or_create_customer(request)
        if customer:
            process_request = process_order_request(request, customer)
            serializer = CreateOrderSerializer(data=process_request)
            if serializer.is_valid():
                serializer.save()
                return Response(data={"message": "Order created."}, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response(
                    data={"message": "Unable to create Order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
