from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager
from materials.models import Course, Lesson


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


class Payments(models.Model):
    """Модель платежей"""

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Наличные')
        TRANSFER = 'transfer', _('Перевод на счет')

    user = models.ForeignKey(
        User,  # Ссылка на модель User из этого же файла
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('пользователь')
    )
    payment_date = models.DateTimeField(
        _('дата оплаты'),
        auto_now_add=True
    )
    paid_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('оплаченный курс')
    )
    paid_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('оплаченный урок')
    )
    amount = models.DecimalField(
        _('сумма оплаты'),
        max_digits=10,
        decimal_places=2
    )
    payment_method = models.CharField(
        _('способ оплаты'),
        max_length=10,
        choices=PaymentMethod.choices
    )

    class Meta:
        verbose_name = _('платеж')
        verbose_name_plural = _('платежи')
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.payment_date}"