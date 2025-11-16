# courses/api_urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

app_name = "courses_api"

router = DefaultRouter()
# Здесь позже зарегистрируем ViewSets

urlpatterns = [
    # API endpoints будут здесь
]

urlpatterns += router.urls
