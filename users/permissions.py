from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class IsModerator(permissions.BasePermission):
    """
    Права доступа для модераторов.
    Модераторы могут просматривать и изменять любой контент, но не могут создавать и удалять.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        # Разрешаем доступ только аутентифицированным пользователям
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем, является ли пользователь модератором
        return bool(request.user.groups.filter(name="moderators").exists())  # ← ЯВНОЕ ПРЕОБРАЗОВАНИЕ


class IsOwner(permissions.BasePermission):
    """
    Права доступа для владельцев объектов.
    Владельцы могут делать все со своими объектами.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # Проверяем, является ли пользователь владельцем объекта
        if hasattr(obj, "owner"):
            return obj.owner == request.user  # type: ignore
        return False


class IsOwnerOrModerator(permissions.BasePermission):
    """
    Права доступа для владельцев или модераторов.
    Владельцы могут делать все со своими объектами, модераторы - только просмотр и изменение.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # Владелец может делать все со своим объектом
        if hasattr(obj, "owner") and obj.owner == request.user:
            return True

        # Модераторы могут только просматривать и изменять (PUT/PATCH)
        if request.user.groups.filter(name="moderators").exists():
            if request.method in permissions.SAFE_METHODS + ["PUT", "PATCH"]:
                return True
            else:
                return False  # Запрещаем DELETE для модераторов

        return False


class CanCreateContent(permissions.BasePermission):
    """
    Права доступа для создания контента.
    Запрещает создание модераторам.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method == "POST":
            # Модераторы не могут создавать новый контент
            if request.user.groups.filter(name="moderators").exists():
                return False
        return True


class CanDeleteContent(permissions.BasePermission):
    """
    Права доступа для удаления контента.
    Разрешает удаление только владельцам и админам.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if request.method == "DELETE":
            # Владелец может удалять свой контент
            if hasattr(obj, "owner") and obj.owner == request.user:
                return True
            # Админы могут удалять любой контент
            if request.user.is_staff:
                return True
            # Модераторы не могут удалять
            return False
        return True


class CanViewUserProfile(permissions.BasePermission):
    """
    Права доступа для просмотра профилей пользователей.
    Любой авторизованный пользователь может просматривать любой профиль,
    но с ограниченной информацией.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        # Разрешаем доступ только аутентифицированным пользователям
        return bool(request.user and request.user.is_authenticated)  # ← ЯВНОЕ ПРЕОБРАЗОВАНИЕ

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # Любой авторизованный пользователь может просматривать любой профиль
        if request.method in permissions.SAFE_METHODS:
            return True
        return False


class CanEditUserProfile(permissions.BasePermission):
    """
    Права доступа для редактирования профилей пользователей.
    Пользователь может редактировать только свой профиль.
    Модераторы и админы могут редактировать любой профиль.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # Пользователь может редактировать только свой профиль
        if obj == request.user:
            return True

        # Модераторы и админы могут редактировать любой профиль
        if request.user.groups.filter(name="moderators").exists() or request.user.is_staff:
            return True

        return False


class IsModeratorOrAdmin(permissions.BasePermission):
    """
    Права доступа для модераторов и админов.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(  # ← ЯВНОЕ ПРЕОБРАЗОВАНИЕ
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.groups.filter(name="moderators").exists())
        )
