from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentsViewSet, UserViewSet

app_name = "users_api"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"payments", PaymentsViewSet, basename="payments")

urlpatterns = [
    path("", include(router.urls)),
]
