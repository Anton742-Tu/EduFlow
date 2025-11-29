from typing import Optional

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
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


@extend_schema(
    summary="Тестовый эндпоинт API",
    description="Простой тестовый эндпоинт для проверки работы API.",
    tags=["utils"],
    responses={
        200: {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "EduFlow API работает!"},
                "status": {"type": "string", "example": "success"},
                "version": {"type": "string", "example": "1.0"},
            },
        }
    },
)
@api_view(["GET"])
def test_api(request: Request) -> Response:
    """Простой тестовый API endpoint"""
    return Response({"message": "EduFlow API работает!", "status": "success", "version": "1.0"})


@extend_schema_view(
    list=extend_schema(
        summary="Список курсов",
        description="Получить список курсов. Пользователи видят только свои курсы, модераторы и администраторы - все.",
        tags=["courses"],
        parameters=[
            OpenApiParameter(
                name="page", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Номер страницы"
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Количество элементов на странице (макс. 100)",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Детали курса",
        description="Получить детальную информацию о курсе. Доступно владельцу, модераторам и администраторам.",
        tags=["courses"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID курса")
        ],
    ),
    create=extend_schema(
        summary="Создание курса",
        description="Создать новый курс. Доступно обычным пользователям (не модераторам).",
        tags=["courses"],
    ),
    update=extend_schema(
        summary="Обновление курса",
        description="Обновить курс. Доступно владельцу, модераторам и администраторам.",
        tags=["courses"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID курса")
        ],
    ),
    partial_update=extend_schema(
        summary="Частичное обновление курса",
        description="Частичное обновление курса. Доступно владельцу, модераторам и администраторам.",
        tags=["courses"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID курса")
        ],
    ),
    destroy=extend_schema(
        summary="Удаление курса",
        description="Удалить курс. Доступно только владельцу или администраторам.",
        tags=["courses"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID курса")
        ],
    ),
)
class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с курсами.
    Обычные пользователи видят и редактируют только свои курсы.
    Модераторы видят и редактируют все курсы, но не могут создавать/удалять.
    """

    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Course.objects.none()  # Фикс для drf-spectacular

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
        # Фикс для drf-spectacular
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()

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

    @extend_schema(
        summary="Подписаться на курс",
        description="Подписаться на обновления курса. Получать уведомления о новых уроках.",
        tags=["courses"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID курса")
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Подписка оформлена"},
                    "course": {"type": "string", "example": "Название курса"},
                    "subscribed": {"type": "boolean", "example": True},
                    "created": {"type": "boolean", "example": True},
                },
            }
        },
    )
    @action(detail=True, methods=["post"])
    def subscribe(self, request: Request, pk: Optional[str] = None) -> Response:
        """Эндпоинт для подписки на курс"""
        course = self.get_object()
        user = request.user

        # Создаем подписку (get_or_create сам проверит существование)
        subscription, created = Subscription.objects.get_or_create(user=user, course=course)

        return Response(
            {"message": "Подписка оформлена", "course": course.title, "subscribed": True, "created": created},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Отписаться от курса",
        description="Отписаться от обновлений курса.",
        tags=["courses"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID курса")
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Подписка отменена"},
                    "course": {"type": "string", "example": "Название курса"},
                    "subscribed": {"type": "boolean", "example": False},
                },
            },
            404: {"type": "object", "properties": {"message": {"type": "string", "example": "Подписка не найдена"}}},
        },
    )
    @action(detail=True, methods=["post"])
    def unsubscribe(self, request: Request, pk: Optional[str] = None) -> Response:
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


@extend_schema_view(
    list=extend_schema(
        summary="Список уроков",
        description="Получить список уроков. Пользователи видят только свои уроки, модераторы и администраторы - все.",
        tags=["lessons"],
        parameters=[
            OpenApiParameter(
                name="page", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Номер страницы"
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Количество элементов на странице (макс. 100)",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Детали урока",
        description="Получить детальную информацию об уроке. Доступно владельцу, модераторам и администраторам.",
        tags=["lessons"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID урока")
        ],
    ),
    create=extend_schema(
        summary="Создание урока",
        description="Создать новый урок. Доступно обычным пользователям. Автоматическая валидация YouTube ссылок.",
        tags=["lessons"],
    ),
    update=extend_schema(
        summary="Обновление урока",
        description="Обновить урок. Доступно владельцу, модераторам и администраторам.",
        tags=["lessons"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID урока")
        ],
    ),
    partial_update=extend_schema(
        summary="Частичное обновление урока",
        description="Частичное обновление урока. Доступно владельцу, модераторам и администраторам.",
        tags=["lessons"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID урока")
        ],
    ),
    destroy=extend_schema(
        summary="Удаление урока",
        description="Удалить урок. Доступно только владельцу или администраторам.",
        tags=["lessons"],
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="ID урока")
        ],
    ),
)
class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с уроками.
    Обычные пользователи видят и редактируют только свои уроки.
    Модераторы видят и редактируют все уроки, но не могут создавать/удалять.
    """

    serializer_class = LessonSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Lesson.objects.all()  # Уже установлен

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
        # Фикс для drf-spectacular
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

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
