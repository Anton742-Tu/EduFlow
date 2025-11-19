from typing import Any, List, Type

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import PaymentsFilter
from .models import Payments, User
from .serializers import PaymentsSerializer, UserCreateSerializer, UserProfileSerializer, UserUpdateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей.
    Предоставляет полный CRUD для пользователей.
    """

    queryset = User.objects.all().prefetch_related("payments")

    def get_serializer_class(self) -> Type[UserProfileSerializer | UserUpdateSerializer | UserCreateSerializer]:
        """Выбираем сериализатор в зависимости от действия"""
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserProfileSerializer

    def get_permissions(self) -> List[AllowAny]:
        """Разрешаем создание пользователей без авторизации"""
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()  # type: ignore  # ← Игнорируем сложный тип

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        """Эндпоинт для получения текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "patch"])
    def update_me(self, request: Request) -> Response:
        """Эндпоинт для обновления текущего пользователя"""
        serializer = self.get_serializer(request.user, data=request.data, partial=request.method == "PATCH")
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PaymentsViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления платежами с фильтрацией и сортировкой.
    """

    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PaymentsFilter
    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]
