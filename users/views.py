from typing import Any, Type

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import PaymentsFilter
from .models import Payments, Subscription, User
from .permissions import CanEditUserProfile, IsModeratorOrAdmin
from .serializers import (
    PaymentsSerializer,
    PrivateUserProfileSerializer,
    PublicUserProfileSerializer,
    SubscriptionSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей.
    - Любой авторизованный пользователь может просматривать любой профиль
    - Редактировать можно только свой профиль (кроме модераторов и админов)
    - При просмотре чужого профиля показывается ограниченная информация
    """

    queryset = User.objects.all().prefetch_related("payments")

    def get_permissions(self) -> list:
        """
        Настраиваем права доступа:
        - Регистрация доступна всем
        - Просмотр списка: админы и модераторы
        - Просмотр профиля: любой авторизованный пользователь
        - Редактирование: владелец профиля, модераторы, админы
        """
        if self.action == "create":
            return [AllowAny()]
        elif self.action == "list":
            return [IsAuthenticated(), IsModeratorOrAdmin()]
        elif self.action in ["retrieve"]:
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), CanEditUserProfile()]
        elif self.action in ["me", "update_me"]:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_serializer_class(self) -> Type:
        """Выбираем сериализатор в зависимости от действия и контекста"""
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update", "update_me"]:
            return UserUpdateSerializer
        elif self.action == "retrieve":
            # Определяем какой сериализатор использовать для просмотра
            if self.is_own_profile():
                return PrivateUserProfileSerializer
            else:
                return PublicUserProfileSerializer
        elif self.action in ["me"]:
            return PrivateUserProfileSerializer
        return PublicUserProfileSerializer

    def get_queryset(self) -> QuerySet[User]:
        """
        Админы видят всех пользователей.
        Обычные пользователи при запросе списка получают пустой результат.
        """
        user = self.request.user

        if not user.is_authenticated:
            return User.objects.none()

        if user.is_staff:
            return User.objects.all().prefetch_related("payments")
        elif self.action == "list":
            # Обычные пользователи не видят список всех пользователей
            return User.objects.none()
        else:
            return User.objects.all().prefetch_related("payments")

    def is_own_profile(self) -> bool:
        """
        Проверяет, запрашивает ли пользователь свой собственный профиль.
        """
        try:
            if not hasattr(self, "kwargs") or "pk" not in self.kwargs:
                return False

            profile_id = self.kwargs["pk"]

            # Обрабатываем случай, когда pk = 'me'
            if profile_id == "me":
                return True

            # Проверяем, что пользователь аутентифицирован
            if not self.request.user.is_authenticated:
                return False

            # Явное преобразование и сравнение
            user_id: int = self.request.user.id
            profile_id_int: int = int(profile_id)
            return user_id == profile_id_int

        except (ValueError, TypeError):
            return False

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        """Эндпоинт для получения текущего пользователя (полная информация)"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "patch"])
    def update_me(self, request: Request) -> Response:
        """Эндпоинт для обновления текущего пользователя"""
        serializer = self.get_serializer(request.user, data=request.data, partial=request.method == "PATCH")
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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
    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]

    def get_permissions(self) -> list:
        """
        Права доступа для платежей:
        - Просмотр: владелец платежа, модераторы, админы
        - Создание/изменение/удаление: админы
        """
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self) -> QuerySet[Payments]:
        """
        Обычные пользователи видят только свои платежи.
        Модераторы и админы видят все платежи.
        """
        user = self.request.user
        if not user.is_authenticated:
            return Payments.objects.none()

        if user.is_staff or user.groups.filter(name="moderators").exists():
            return Payments.objects.all()
        else:
            return Payments.objects.filter(user=user)

    def perform_create(self, serializer: PaymentsSerializer) -> None:
        """Автоматически назначаем пользователя при создании платежа"""
        if not self.request.user.is_staff:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().create(request, *args, **kwargs)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().retrieve(request, *args, **kwargs)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().update(request, *args, **kwargs)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().destroy(request, *args, **kwargs)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления подписками на курсы
    """

    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Subscription]:
        """Пользователь видит только свои подписки"""
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer: SubscriptionSerializer) -> None:
        """Автоматически назначаем пользователя при создании подписки"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def subscribe(self, request: Request) -> Response:
        """Эндпоинт для подписки на курс"""
        course_id = request.data.get("course_id")

        if not course_id:
            return Response({"error": "course_id обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from materials.models import Course

            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Курс не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, не подписан ли уже пользователь
        if Subscription.objects.filter(user=request.user, course=course).exists():
            return Response({"error": "Вы уже подписаны на этот курс"}, status=status.HTTP_400_BAD_REQUEST)

        # Создаем подписку
        subscription = Subscription.objects.create(user=request.user, course=course)

        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def unsubscribe(self, request: Request) -> Response:
        """Эндпоинт для отписки от курса"""
        course_id = request.data.get("course_id")

        if not course_id:
            return Response({"error": "course_id обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = Subscription.objects.get(user=request.user, course_id=course_id)
        except Subscription.DoesNotExist:
            return Response({"error": "Подписка не найдена"}, status=status.HTTP_404_NOT_FOUND)

        subscription.delete()
        return Response({"message": "Вы успешно отписались от курса"}, status=status.HTTP_200_OK)
