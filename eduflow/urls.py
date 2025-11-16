from django.contrib import admin
from django.urls import path, include
from materials.views import home  # Добавляем импорт

urlpatterns = [
    path('', home, name='home'),  # Главная страница
    path('admin/', admin.site.urls),
    path('api/', include('materials.api_urls')),  # API маршруты
    path('api/', include('users.api_urls')),
    path('api-auth/', include('rest_framework.urls')),  # Логин для API
]