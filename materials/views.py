from typing import Any

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from users.permissions import IsOwnerOrModerator, CanCreateContent, IsModerator
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer


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
    """
    queryset = Course.objects.all().prefetch_related('lessons')
    serializer_class = CourseSerializer

    def get_permissions(self):
        """
        Права доступа для курсов:
        - Создание: обычные пользователи (не модераторы)
        - Просмотр: все авторизованные
        - Изменение/Удаление: владелец или админ
        """
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateContent()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrModerator()]
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Все авторизованные пользователи видят все курсы
        """
        return Course.objects.all().prefetch_related('lessons')

    def perform_create(self, serializer):
        """
        При создании курса автоматически устанавливаем владельца
        """
        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic-класс для получения списка уроков и создания нового урока
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), CanCreateContent()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """
    Generic-класс для получения одного урока
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]


class LessonUpdateAPIView(generics.UpdateAPIView):
    """
    Generic-класс для обновления урока
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrModerator]


class LessonDestroyAPIView(generics.DestroyAPIView):
    """
    Generic-класс для удаления урока
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrModerator]
