from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import test_api

app_name = 'materials_api'

router = DefaultRouter()

urlpatterns = [
    path('test/', test_api, name='test-api'),
]

urlpatterns += router.urls