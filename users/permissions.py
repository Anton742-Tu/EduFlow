from typing import Any

from django.db.models import Model
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
    Разрешение для владельца объекта или модератора.
    Модераторы могут просматривать и редактировать, но не создавать/удалять.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Model) -> bool:
        """
        Проверяет права доступа к конкретному объекту.
        """
        # Разрешаем безопасные методы (GET, HEAD, OPTIONS) для всех авторизованных
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для PUT, PATCH - разрешаем владельцу или модератору
        if request.method in ["PUT", "PATCH"]:
            can_edit: bool = (
                obj.owner == request.user
                or request.user.groups.filter(name="moderators").exists()
                or request.user.is_staff
            )
            return can_edit

        # Для DELETE - только владелец или админ
        if request.method == "DELETE":
            can_delete: bool = obj.owner == request.user or request.user.is_staff
            return can_delete

        return False


class CanCreateContent(permissions.BasePermission):
    """
    Разрешение на создание контента.
    Обычные пользователи могут создавать, модераторы - нет.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """
        Проверяет права доступа для создания контента.
        """
        # Модераторы не могут создавать контент
        if request.user.groups.filter(name="moderators").exists():
            return False
        return True


class CanDeleteContent(permissions.BasePermission):
    """
    Разрешение на удаление контента.
    Только владельцы или администраторы могут удалять.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Model) -> bool:
        """
        Проверяет права доступа для удаления объекта.
        """
        can_delete_object: bool = obj.owner == request.user or request.user.is_staff
        return can_delete_object


class CanViewUserProfile(permissions.BasePermission):
    """
    Права доступа для просмотра профилей пользователей.
    Любой авторизованный пользователь может просматривать любой профиль,
    но с ограниченной информацией.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        # Разрешаем доступ только аутентифицированным пользователям
        return bool(request.user and request.user.is_authenticated)

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
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.groups.filter(name="moderators").exists())
        )
