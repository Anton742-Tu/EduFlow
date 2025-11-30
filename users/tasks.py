import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from materials.models import Course, Lesson

from .models import Payments, Subscription, User

logger = logging.getLogger(__name__)


@shared_task
def send_course_update_notification(course_id, lesson_title):
    """
    Отправка уведомлений подписчикам о новом уроке в курсе
    """
    try:
        course = Course.objects.get(id=course_id)
        subscriptions = Subscription.objects.filter(course=course)

        for subscription in subscriptions:
            subject = f'Новый урок в курсе "{course.title}"'
            message = f'В курсе "{course.title}" добавлен новый урок: "{lesson_title}"'

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [subscription.user.email],
                fail_silently=False,
            )

        logger.info(f"Уведомления отправлены для курса {course.title}")
        return f"Уведомления отправлены {subscriptions.count()} подписчикам"

    except Exception as e:
        logger.error(f"Ошибка отправки уведомлений: {e}")
        return f"Ошибка: {e}"


@shared_task
def check_payment_status():
    """
    Проверка статуса pending платежей
    """
    try:
        pending_payments = Payments.objects.filter(
            payment_status="pending", payment_date__lte=datetime.now() - timedelta(hours=24)
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
def cleanup_old_data():
    """
    Очистка старых данных (например, логи, временные файлы)
    """
    try:
        # Пример: удаление платежей старше 1 года со статусом failed
        from datetime import datetime, timedelta

        old_date = datetime.now() - timedelta(days=365)

        deleted_count = Payments.objects.filter(payment_status="failed", payment_date__lte=old_date).delete()[0]

        logger.info(f"Удалено {deleted_count} старых записей")
        return f"Удалено {deleted_count} записей"

    except Exception as e:
        logger.error(f"Ошибка очистки данных: {e}")
        return f"Ошибка: {e}"
