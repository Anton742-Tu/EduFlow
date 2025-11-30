import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Setup periodic tasks for Celery Beat"

    def handle(self, *args, **options):
        # Создание интервалов
        every_5_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )

        # Тестовая задача для проверки email
        PeriodicTask.objects.get_or_create(
            interval=every_5_minutes,
            name="Test email sending",
            task="users.tasks.send_welcome_email",
            kwargs=json.dumps({"user_id": 1}),  # Заменить на реальный ID пользователя
            enabled=False,  # Отключена по умолчанию
            defaults={"description": "Тестовая задача отправки email"},
        )

        every_hour, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        every_day, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        # Задача: проверка статуса платежей каждый час
        PeriodicTask.objects.get_or_create(
            interval=every_hour,
            name="Check payment status",
            task="users.tasks.check_payment_status",
            defaults={"description": "Проверка статуса pending платежей"},
        )

        # Задача: очистка старых данных каждый день
        PeriodicTask.objects.get_or_create(
            interval=every_day,
            name="Cleanup old data",
            task="users.tasks.cleanup_old_data",
            defaults={"description": "Очистка старых данных"},
        )

        self.stdout.write(self.style.SUCCESS("Successfully setup periodic tasks"))
