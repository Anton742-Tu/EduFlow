from typing import Any

from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Setup periodic tasks for Celery Beat"

    def handle(self, *args: Any, **options: Any) -> None:
        # Создание интервалов
        every_10_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )

        every_hour, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        every_day, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        every_week, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        # Задача: проверка статуса платежей каждый час
        PeriodicTask.objects.get_or_create(
            interval=every_hour,
            name="Check payment status hourly",
            task="users.tasks.check_payment_status",
            defaults={"description": "Проверка статуса pending платежей каждый час"},
        )

        # Задача: очистка старых данных каждый день
        PeriodicTask.objects.get_or_create(
            interval=every_day,
            name="Cleanup old data daily",
            task="users.tasks.cleanup_old_data",
            defaults={"description": "Очистка старых данных каждый день"},
        )

        # Задача: деактивация неактивных пользователей каждую неделю
        PeriodicTask.objects.get_or_create(
            interval=every_week,
            name="Deactivate inactive users weekly",
            task="users.tasks.deactivate_inactive_users",
            defaults={
                "description": "Деактивация пользователей, не заходивших более 30 дней (еженедельно)",
                "enabled": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Successfully setup periodic tasks"))
