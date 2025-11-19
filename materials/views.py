from typing import Any

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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
    Предоставляет все стандартные действия: list, create, retrieve, update, partial_update, destroy
    """

    queryset = Course.objects.all().prefetch_related("lessons")
    serializer_class = CourseSerializer


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic-класс для получения списка уроков и создания нового урока
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """
    Generic-класс для получения одного урока
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonUpdateAPIView(generics.UpdateAPIView):
    """
    Generic-класс для обновления урока
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonDestroyAPIView(generics.DestroyAPIView):
    """
    Generic-класс для удаления урока
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
