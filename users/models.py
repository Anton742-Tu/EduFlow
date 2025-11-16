from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class User(AbstractUser):
    # Убираем поле username и делаем email как основное для аутентификации
    username = None
    email = models.EmailField(_("email address"), unique=True)

    # Дополнительные поля
    phone = models.CharField(_("phone number"), max_length=20, blank=True, null=True)
    city = models.CharField(_("city"), max_length=100, blank=True, null=True)
    avatar = models.ImageField(
        _("avatar"), upload_to="users/avatars/", blank=True, null=True, help_text=_("Upload your profile picture")
    )

    # Устанавливаем кастомный менеджер
    objects = CustomUserManager()

    # Устанавливаем email как поле для аутентификации
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Убираем email из REQUIRED_FIELDS

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Возвращает полное имя пользователя."""
        return f"{self.first_name} {self.last_name}".strip()
