from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from materials.views import home

urlpatterns = [
    path("", home, name="home"),  # Главная страница
    path("admin/", admin.site.urls),
    path("api/", include("materials.api_urls")),  # API маршруты
    path("api/", include("users.api_urls")),
    path("api/auth/", include("users.jwt_urls")),  # JWT URLs
    path("api-auth/", include("rest_framework.urls")),  # Логин для API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Редирект с docs на redoc (раз Swagger не работает)
    path("api/docs/", RedirectView.as_view(url="/api/redoc/", permanent=False)),
    path("", RedirectView.as_view(url="/api/redoc/", permanent=False)),
]
