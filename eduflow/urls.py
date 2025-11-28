from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from materials.views import home

urlpatterns = [
    path("", home, name="home"),  # Главная страница
    path("admin/", admin.site.urls),
    path("api/", include("materials.api_urls")),  # API маршруты
    path("api/", include("users.api_urls")),
    path("api/auth/", include("users.jwt_urls")),  # JWT URLs
    path("api-auth/", include("rest_framework.urls")),  # Логин для API
    # Документация API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
