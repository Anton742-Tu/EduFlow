from typing import List

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
    USERNAME_FIELD: str = "email"
    REQUIRED_FIELDS: List[str] = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        return str(self.email)

    @property
    def full_name(self) -> str:
        """Возвращает полное имя пользователя."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else str(self.email)


class Payments(models.Model):
    """Модель платежей"""

    class PaymentMethod(models.TextChoices):
        CASH = "cash", _("Наличные")
        TRANSFER = "transfer", _("Перевод на счет")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments", verbose_name=_("пользователь"))
    payment_date = models.DateTimeField(_("дата оплаты"), auto_now_add=True)
    paid_course = models.ForeignKey(
        "materials.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("оплаченный курс"),
    )
    paid_lesson = models.ForeignKey(
        "materials.Lesson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("оплаченный урок"),
    )
    amount = models.DecimalField(_("сумма оплаты"), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_("способ оплаты"), max_length=10, choices=PaymentMethod.choices)

    class Meta:
        verbose_name = _("платеж")
        verbose_name_plural = _("платежи")
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.amount} - {self.payment_date}"

    def clean(self) -> None:
        """Проверяем что оплачен либо курс, либо урок"""
        from django.core.exceptions import ValidationError

        if self.paid_course and self.paid_lesson:
            raise ValidationError(_("Можно оплатить либо курс, либо урок, но не оба одновременно."))
        if not self.paid_course and not self.paid_lesson:
            raise ValidationError(_("Должен быть оплачен либо курс, либо урок."))


class Subscription(models.Model):
    """
    Модель подписки пользователя на обновления курса
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions", verbose_name=_("пользователь")
    )
    course = models.ForeignKey(
        "materials.Course", on_delete=models.CASCADE, related_name="subscriptions", verbose_name=_("курс")
    )
    subscribed_at = models.DateTimeField(_("дата подписки"), auto_now_add=True)

    class Meta:
        verbose_name = _("подписка")
        verbose_name_plural = _("подписки")
        unique_together = ["user", "course"]  # Одна подписка на курс для пользователя
        ordering = ["-subscribed_at"]

    def __str__(self) -> str:
        return f"{self.user.email} подписан на {self.course.title}"
