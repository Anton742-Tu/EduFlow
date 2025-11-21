from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.request import Request
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import User, Payments
from .serializers import (
    PublicUserProfileSerializer,
    PrivateUserProfileSerializer,
    UserUpdateSerializer,
    UserCreateSerializer,
    PaymentsSerializer
)
from .filters import PaymentsFilter
from .permissions import CanViewUserProfile, CanEditUserProfile
from typing import Any, Type, List


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей.
    """
    queryset = User.objects.all().prefetch_related('payments')

    def get_permissions(self):
        """
        Настраиваем права доступа:
        - Регистрация доступна всем
        - Просмотр списка: админы и модераторы
        - Просмотр профиля: любой авторизованный пользователь
        - Редактирование: владелец профиля, модераторы, админы
        """
        if self.action == 'create':
            return [AllowAny()]
        elif self.action == 'list':
            return [IsAuthenticated(), IsAdminUser()]
        elif self.action in ['retrieve']:
            return [IsAuthenticated(), CanViewUserProfile()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanEditUserProfile()]
        elif self.action in ['me', 'update_me']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия и контекста"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update', 'update_me']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            # Определяем какой сериализатор использовать для просмотра
            if self.is_own_profile():
                return PrivateUserProfileSerializer
            else:
                return PublicUserProfileSerializer
        elif self.action in ['me']:
            return PrivateUserProfileSerializer
        return PublicUserProfileSerializer

    def get_queryset(self):
        """
        Админы видят всех пользователей.
        Обычные пользователи при запросе списка получают пустой результат.
        """
        if self.request.user.is_staff:
            return User.objects.all().prefetch_related('payments')
        elif self.action == 'list':
            # Обычные пользователи не видят список всех пользователей
            return User.objects.none()
        else:
            return User.objects.all().prefetch_related('payments')

    def is_own_profile(self):
        """
        Проверяет, запрашивает ли пользователь свой собственный профиль.
        """
        if hasattr(self, 'kwargs') and 'pk' in self.kwargs:
            return str(self.request.user.id) == self.kwargs['pk']
        return False

    @action(detail=False, methods=['get'])
    def me(self, request: Request) -> Response:
        """Эндпоинт для получения текущего пользователя (полная информация)"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
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

    def retrieve(self, request, *args, **kwargs):
        """
        Переопределяем retrieve для логирования просмотров профилей
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Логируем просмотр чужого профиля
        if not self.is_own_profile():
            print(f"Пользователь {request.user.email} просматривает профиль {instance.email}")

        return Response(serializer.data)


class PaymentsViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления платежами с фильтрацией и сортировкой.
    """
    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PaymentsFilter
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']

    def get_permissions(self):
        """
        Права доступа для платежей:
        - Просмотр: владелец платежа, модераторы, админы
        - Создание/изменение/удаление: админы
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        """
        Обычные пользователи видят только свои платежи.
        Модераторы и админы видят все платежи.
        """
        user = self.request.user
        if user.is_staff or user.groups.filter(name='moderators').exists():
            return Payments.objects.all()
        else:
            return Payments.objects.filter(user=user)
