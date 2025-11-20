from rest_framework import permissions
from django.contrib.auth.models import Group


class IsModerator(permissions.BasePermission):
    """
    Права доступа для модераторов.
    Модераторы могут просматривать и изменять любой контент, но не могут создавать и удалять.
    """

    def has_permission(self, request, view):
        # Разрешаем доступ только аутентифицированным пользователям
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем, является ли пользователь модератором
        return request.user.groups.filter(name='moderators').exists()

    def has_object_permission(self, request, view, obj):
        # Модераторы могут просматривать и изменять любой объект
        if request.method in permissions.SAFE_METHODS + ['PUT', 'PATCH']:
            return request.user.groups.filter(name='moderators').exists()

        # Модераторы не могут удалять объекты
        if request.method == 'DELETE':
            return False

        return False


class IsOwnerOrModerator(permissions.BasePermission):
    """
    Права доступа для владельцев или модераторов.
    Владельцы могут делать все со своими объектами, модераторы - только просмотр и изменение.
    """

    def has_object_permission(self, request, view, obj):
        # Владелец может делать все со своим объектом
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True

        # Модераторы могут только просматривать и изменять
        if request.user.groups.filter(name='moderators').exists():
            if request.method in permissions.SAFE_METHODS + ['PUT', 'PATCH']:
                return True

        return False


class CanCreateContent(permissions.BasePermission):
    """
    Права доступа для создания контента.
    Запрещает создание модераторам.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            # Модераторы не могут создавать новый контент
            if request.user.groups.filter(name='moderators').exists():
                return False
        return True
