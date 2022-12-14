from django.db.models import Prefetch
from rest_framework import status, views, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from orders.models import (
    Order,
    OrderHistory,
)
from orders.serializers import (
    CreateOrderSerializer,
    CreateOrderHistorySerializer,
    OrderListSerializer,
    OrdersSerializer,
)
from orders.services import (
    get_or_create_customer,
    process_order_request,
    process_order_history_request,
    process_attachments,
)
from vanguard.permissions import IsDeveloperUser, IsAdminUser, IsStaffUser

# Orders
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


class CreateOrderView(views.APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        customer = get_or_create_customer(request)
        if customer:
            process_request, attachments = process_order_request(request, customer)
            serializer = CreateOrderSerializer(data=process_request)
            if serializer.is_valid():
                order = serializer.save()
                has_failed_upload = process_attachments(order, attachments)
                if has_failed_upload:
                    return Response(
                        data={"message": "Order created. Failed to upload attachments"},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(data={"message": "Order created."}, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response(
                    data={"message": "Unable to create Order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class CreateOrderHistoryView(views.APIView):
    permission_classes = [IsDeveloperUser | IsAdminUser | IsStaffUser]

    def post(self, request, *args, **kwargs):
        process_order_history = process_order_history_request(request)
        if process_order_history:
            serializer = CreateOrderHistorySerializer(data=process_order_history)
            if serializer.is_valid():
                serializer.save()
                return Response(data={"message": "Order updated."}, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response(
                    data={"message": "Unable to update Order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
