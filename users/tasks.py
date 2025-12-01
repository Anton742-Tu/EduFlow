import logging
from datetime import timedelta
from typing import Optional

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from materials.models import Course

from .models import Payments, Subscription, User

logger = logging.getLogger(__name__)


@shared_task
def send_course_update_notification(
    course_id: int, lesson_title: str, lesson_description: Optional[str] = None
) -> str:
    """
    Асинхронная рассылка уведомлений подписчикам о новом уроке в курсе
    """
    try:
        course = Course.objects.get(id=course_id)
        subscriptions = Subscription.objects.filter(course=course).select_related("user")

        if not subscriptions:
            logger.info(f"Нет подписчиков для курса {course.title}")
            return "Нет подписчиков для уведомления"

        successful_sends = 0
        failed_sends = 0

        for subscription in subscriptions:
            try:
                user = subscription.user

                # Подготовка HTML шаблона письма
                context = {
                    "user_name": user.first_name or user.email,
                    "course_title": course.title,
                    "lesson_title": lesson_title,
                    "lesson_description": lesson_description,
                    "course_url": f"{settings.FRONTEND_URL}/courses/{course.id}",
                    "unsubscribe_url": f"{settings.FRONTEND_URL}/unsubscribe/{subscription.id}",
                }

                html_message = render_to_string("emails/course_update_notification.html", context)
                plain_message = strip_tags(html_message)

                subject = f'🎓 Новый урок в курсе "{course.title}"'

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

                successful_sends += 1
                logger.debug(f"Уведомление отправлено для {user.email}")

            except Exception as e:
                failed_sends += 1
                logger.error(f"Ошибка отправки для {subscription.user.email}: {e}")

        logger.info(f"Рассылка завершена. Успешно: {successful_sends}, Ошибок: {failed_sends}")
        return f"Уведомления отправлены: {successful_sends} подписчикам, ошибок: {failed_sends}"

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден")
        return f"Ошибка: курс с ID {course_id} не найден"
    except Exception as e:
        logger.error(f"Ошибка рассылки уведомлений: {e}")
        return f"Ошибка: {e}"


@shared_task
def send_welcome_email(user_id: int) -> str:
    """
    Отправка приветственного письма новому пользователю
    """
    try:
        user = User.objects.get(id=user_id)

        context = {
            "user_name": user.first_name or "Пользователь",
            "email": user.email,
            "login_url": f"{settings.FRONTEND_URL}/login",
        }

        html_message = render_to_string("emails/welcome_email.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject="🎉 Добро пожаловать в EduFlow!",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )

        logger.info(f"Приветственное письмо отправлено для {user.email}")
        return "Приветственное письмо отправлено"

    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден")
        return "Ошибка: пользователь не найден"
    except Exception as e:
        logger.error(f"Ошибка отправки приветственного письма: {e}")
        return f"Ошибка: {e}"


@shared_task
def check_payment_status() -> str:
    """
    Проверка статуса pending платежей
    """
    try:
        pending_payments = Payments.objects.filter(
            payment_status="pending", payment_date__lte=timezone.now() - timedelta(hours=24)
        )

        updated_count = 0
        for payment in pending_payments:
            payment.payment_status = "failed"
            payment.save()
            updated_count += 1

        logger.info(f"Обновлено {updated_count} просроченных платежей")
        return f"Обновлено {updated_count} платежей"

    except Exception as e:
        logger.error(f"Ошибка проверки платежей: {e}")
        return f"Ошибка: {e}"


@shared_task
def cleanup_old_data() -> str:
    """
    Очистка старых данных (например, логи, временные файлы)
    """
    try:
        # Пример: удаление платежей старше 1 года со статусом failed
        old_date = timezone.now() - timedelta(days=365)

        deleted_count = Payments.objects.filter(payment_status="failed", payment_date__lte=old_date).delete()[0]

        logger.info(f"Удалено {deleted_count} старых записей")
        return f"Удалено {deleted_count} записей"

    except Exception as e:
        logger.error(f"Ошибка очистки данных: {e}")
        return f"Ошибка: {e}"


@shared_task
def deactivate_inactive_users() -> str:
    """
    Фоновая задача для деактивации пользователей, не заходивших более месяца
    """
    try:
        # Дата месяц назад
        month_ago = timezone.now() - timedelta(days=30)

        # Находим пользователей, которые не заходили более месяца и еще активны
        inactive_users = (
            User.objects.filter(last_login__lt=month_ago, is_active=True)
            .exclude(is_staff=True)  # Не блокируем staff пользователей
            .exclude(is_superuser=True)  # Не блокируем суперпользователей
        )

        user_count = inactive_users.count()

        if user_count == 0:
            logger.info("Нет неактивных пользователей для деактивации")
            return "Нет неактивных пользователей для деактивации"

        # Деактивируем пользователей
        deactivated_count = inactive_users.update(is_active=False)

        # Логируем деактивированных пользователей
        deactivated_emails = list(inactive_users.values_list("email", flat=True))

        logger.info(f"Деактивировано {deactivated_count} неактивных пользователей: {deactivated_emails}")

        # Отправляем уведомление администратору (опционально)
        send_admin_notification.delay(
            subject="Отчет о деактивации неактивных пользователей",
            message=f"Было деактивировано {deactivated_count} пользователей, не заходивших более месяца.",
        )

        return f"Деактивировано {deactivated_count} неактивных пользователей"

    except Exception as e:
        logger.error(f"Ошибка при деактивации неактивных пользователей: {e}")
        return f"Ошибка: {e}"


@shared_task
def send_admin_notification(subject: str, message: str) -> str:
    """
    Отправка уведомления администратору
    """
    try:
        # Получаем email администратора из настроек или используем первый staff email
        admin_user = User.objects.filter(is_staff=True).first()

        if admin_user and admin_user.email:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_user.email],
                fail_silently=False,
            )
            logger.info(f"Уведомление администратору отправлено: {subject}")
            return "Уведомление администратору отправлено"
        else:
            logger.warning("Не найден email администратора для отправки уведомления")
            return "Не найден email администратора"

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления администратору: {e}")
        return f"Ошибка: {e}"
