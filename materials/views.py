from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import Subscription
from users.permissions import CanCreateContent, CanDeleteContent, IsOwnerOrModerator

from .models import Course, Lesson
from .paginators import StandardResultsSetPagination
from .serializers import CourseSerializer, LessonSerializer


def home(request: HttpRequest) -> HttpResponse:
    return HttpResponse(
        "<h1>EduFlow - Образовательная платформа</h1>"
        "<p>Добро пожаловать в EduFlow! Платформа для создания и прохождения курсов.</p>"
        "<p><a href='/admin/'>Перейти в админку</a></p>"
        "<p><a href='/api/'>API Root</a></p>"
    )


@api_view(["GET"])
def test_api(request: Request) -> Response:
    """Простой тестовый API endpoint"""
    return Response({"message": "EduFlow API работает!", "status": "success", "version": "1.0"})


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с курсами.
    Обычные пользователи видят и редактируют только свои курсы.
    Модераторы видят и редактируют все курсы, но не могут создавать/удалять.
    """

    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self) -> list:
        """
        Права доступа для курсов:
        - Создание: обычные пользователи (не модераторы)
        - Просмотр списка: все авторизованные (видят только свои, кроме модераторов)
        - Просмотр деталей: владелец или модератор
        - Изменение: владелец или модератор
        - Удаление: только владелец или админ
        """
        if self.action == "create":
            return [IsAuthenticated(), CanCreateContent()]
        elif self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsOwnerOrModerator()]
        elif self.action == "destroy":
            return [IsAuthenticated(), CanDeleteContent()]
        elif self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self) -> QuerySet[Course]:
        """
        Обычные пользователи видят только свои курсы.
        Модераторы и админы видят все курсы.
        """
        user = self.request.user

        if user.is_staff or user.groups.filter(name="moderators").exists():
            # Модераторы и админы видят все курсы
            return Course.objects.all().prefetch_related("lessons")
        else:
            # Обычные пользователи видят только свои курсы
            return Course.objects.filter(owner=user).prefetch_related("lessons")

    def perform_create(self, serializer: CourseSerializer) -> None:
        """
        При создании курса автоматически устанавливаем владельца
        """
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def subscribe(self, request: Request, pk: str = None) -> Response:
        """Эндпоинт для подписки на курс"""
        course = self.get_object()
        user = request.user

        # Создаем подписку (get_or_create сам проверит существование)
        subscription, created = Subscription.objects.get_or_create(user=user, course=course)

        return Response(
            {"message": "Подписка оформлена", "course": course.title, "subscribed": True, "created": created},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def unsubscribe(self, request: Request, pk: str = None) -> Response:
        """Эндпоинт для отписки от курса"""
        course = self.get_object()
        user = request.user

        try:
            subscription = Subscription.objects.get(user=user, course=course)
            subscription.delete()
            return Response(
                {"message": "Подписка отменена", "course": course.title, "subscribed": False},
                status=status.HTTP_200_OK,
            )
        except Subscription.DoesNotExist:
            return Response({"message": "Подписка не найдена"}, status=status.HTTP_404_NOT_FOUND)


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с уроками.
    Обычные пользователи видят и редактируют только свои уроки.
    Модераторы видят и редактируют все уроки, но не могут создавать/удалять.
    """

    serializer_class = LessonSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Lesson.objects.all()

    def get_permissions(self) -> list:
        """
        Права доступа для уроков:
        - Создание: обычные пользователи (не модераторы)
        - Просмотр списка: все авторизованные (видят только свои, кроме модераторов)
        - Просмотр деталей: владелец или модератор
        - Изменение: владелец или модератор
        - Удаление: только владелец или админ
        """
        if self.action == "create":
            return [IsAuthenticated(), CanCreateContent()]
        elif self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsOwnerOrModerator()]
        elif self.action == "destroy":
            return [IsAuthenticated(), CanDeleteContent()]
        elif self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self) -> QuerySet[Lesson]:
        """
        Обычные пользователи видят только свои уроки.
        Модераторы и админы видят все уроки.
        Переопределяем базовый queryset для фильтрации по владельцу.
        """
        user = self.request.user

        if user.is_staff or user.groups.filter(name="moderators").exists():
            return Lesson.objects.all().select_related("course", "owner")
        else:
            return Lesson.objects.filter(owner=user).select_related("course", "owner")

    def perform_create(self, serializer: LessonSerializer) -> None:
        """
        При создании урока автоматически устанавливаем владельца
        """
        serializer.save(owner=self.request.user)
