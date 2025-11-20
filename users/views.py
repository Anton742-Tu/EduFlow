from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.request import Request
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Payments
from .serializers import UserProfileSerializer, UserUpdateSerializer, UserCreateSerializer, PaymentsSerializer
from .filters import PaymentsFilter
from typing import Any, Type, List


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей с JWT авторизацией.
    """
    queryset = User.objects.all().prefetch_related('payments')

    def get_permissions(self):
        """
        Настраиваем права доступа:
        - Регистрация доступна всем
        - Просмотр списка только админам
        - Просмотр/редактирование своего профиля - авторизованным пользователям
        """
        if self.action == 'create':
            return [AllowAny()]
        elif self.action == 'list':
            return [IsAdminUser()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'me', 'update_me']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserProfileSerializer

    def get_queryset(self):
        """
        Обычные пользователи видят только свой профиль
        Админы видят всех пользователей
        """
        if self.request.user.is_staff:
            return User.objects.all().prefetch_related('payments')
        return User.objects.filter(id=self.request.user.id).prefetch_related('payments')

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request: Request) -> Response:
        """Эндпоинт для получения текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_me(self, request: Request) -> Response:
        """Эндпоинт для обновления текущего пользователя"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
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
