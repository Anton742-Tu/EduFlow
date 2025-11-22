from django.http import HttpResponse
from rest_framework import viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsOwnerOrModerator, CanCreateContent, CanDeleteContent


def home(request: Any) -> HttpResponse:
    return HttpResponse(
        "<h1>EduFlow - Образовательная платформа</h1>"
        "<p>Добро пожаловать в EduFlow! Платформа для создания и прохождения курсов.</p>"
        "<p><a href='/admin/'>Перейти в админку</a></p>"
        "<p><a href='/api/'>API Root</a></p>"
    )


@api_view(["GET"])
def test_api(request: Any) -> Response:
    """Простой тестовый API endpoint"""
    return Response({"message": "EduFlow API работает!", "status": "success", "version": "1.0"})


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с курсами.
    Обычные пользователи видят и редактируют только свои курсы.
    Модераторы видят и редактируют все курсы, но не могут создавать/удалять.
    """

    serializer_class = CourseSerializer

    def get_permissions(self):
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

    def get_queryset(self):
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

    def perform_create(self, serializer):
        """
        При создании курса автоматически устанавливаем владельца
        """
        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic-класс для получения списка уроков и создания нового урока.
    Обычные пользователи видят только свои уроки.
    """

    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateContent()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Обычные пользователи видят только свои уроки.
        Модераторы и админы видят все уроки.
        """
        user = self.request.user

        if user.is_staff or user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        else:
            return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """
    Generic-класс для получения одного урока.
    Доступно владельцам и модераторам.
    """

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrModerator]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        else:
            return Lesson.objects.filter(owner=user)


class LessonUpdateAPIView(generics.UpdateAPIView):
    """
    Generic-класс для обновления урока.
    Доступно владельцам и модераторам.
    """

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrModerator]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        else:
            return Lesson.objects.filter(owner=user)


class LessonDestroyAPIView(generics.DestroyAPIView):
    """
    Generic-класс для удаления урока.
    Доступно только владельцам и админам.
    """

    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, CanDeleteContent]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Lesson.objects.all()
        else:
            return Lesson.objects.filter(owner=user)
