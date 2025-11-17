from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import User
from .serializers import UserCreateSerializer, UserProfileSerializer, UserUpdateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей.
    Предоставляет полный CRUD для пользователей.
    """

    queryset = User.objects.all()

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserProfileSerializer

    def get_permissions(self):
        """Разрешаем создание пользователей без авторизации"""
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Эндпоинт для получения текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "patch"])
    def update_me(self, request):
        """Эндпоинт для обновления текущего пользователя"""
        serializer = self.get_serializer(request.user, data=request.data, partial=request.method == "PATCH")
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
