from typing import List

from django.conf import settings
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
    PAYMENT_METHOD_CHOICES = [
        ("cash", "Наличные"),
        ("transfer", "Перевод"),
        ("stripe", "Stripe"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Ожидает оплаты"),
        ("paid", "Оплачено"),
        ("failed", "Ошибка оплаты"),
        ("refunded", "Возвращено"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments", verbose_name="Пользователь"
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата платежа")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash", verbose_name="Способ оплаты"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending", verbose_name="Статус платежа"
    )
    paid_course = models.ForeignKey(
        "materials.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный курс",
    )
    paid_lesson = models.ForeignKey(
        "materials.Lesson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Оплаченный урок",
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="ID платежа в Stripe"
    )
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID сессии Stripe")

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        return f"Платеж {self.amount} от {self.user.email}"


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_subscriptions",
        verbose_name="Пользователь",
    )
    course = models.ForeignKey(
        "materials.Course", on_delete=models.CASCADE, related_name="course_subscriptions", verbose_name="Курс"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подписки")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ["user", "course"]

    def __str__(self) -> str:
        return f"{self.user.email} подписан на {self.course.title}"
