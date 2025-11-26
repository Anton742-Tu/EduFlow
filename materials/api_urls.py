from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    CourseViewSet,
    test_api,
)

app_name = "materials_api"

router = DefaultRouter()
router.register(r"courses", views.CourseViewSet, basename="courses")
router.register(r"lessons", views.LessonViewSet, basename="lesson")

urlpatterns = [
    path("test/", test_api, name="test-api"),
    # Включаем роутер для курсов (ViewSet)
    path("", include(router.urls)),
]
