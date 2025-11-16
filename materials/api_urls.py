from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    test_api,
    CourseViewSet,
    LessonListCreateAPIView,
    LessonRetrieveAPIView,
    LessonUpdateAPIView,
    LessonDestroyAPIView
)

app_name = 'materials_api'

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')

urlpatterns = [
    path('test/', test_api, name='test-api'),

    # URL для уроков (Generic-классы)
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list-create'),
    path('lessons/<int:pk>/', LessonRetrieveAPIView.as_view(), name='lesson-retrieve'),
    path('lessons/<int:pk>/update/', LessonUpdateAPIView.as_view(), name='lesson-update'),
    path('lessons/<int:pk>/delete/', LessonDestroyAPIView.as_view(), name='lesson-destroy'),

    # Включаем роутер для курсов (ViewSet)
    path('', include(router.urls)),
]