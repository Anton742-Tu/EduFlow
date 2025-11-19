from typing import Any

from django.core.management.base import BaseCommand

from materials.models import Course, Lesson
from users.models import Payments, User


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми платежами"

    def handle(self, *args: Any, **options: Any) -> None:  # ← Добавляем аннотацию
        # Получаем существующие объекты
        users = User.objects.all()
        courses = Course.objects.all()
        lessons = Lesson.objects.all()

        if not users.exists():
            self.stdout.write(self.style.ERROR("Сначала создайте пользователей!"))
            return

        # Создаем тестовые платежи
        payments_data = [
            {
                "user": users[0],
                "paid_course": courses[0] if courses.exists() else None,
                "paid_lesson": None,
                "amount": 10000.00,
                "payment_method": "transfer",
            },
            {
                "user": users[0],
                "paid_course": None,
                "paid_lesson": lessons[0] if lessons.exists() else None,
                "amount": 1500.00,
                "payment_method": "cash",
            },
        ]

        created_count = 0
        for payment_data in payments_data:
            # Проверяем что есть либо курс, либо урок
            if payment_data["paid_course"] or payment_data["paid_lesson"]:
                payment = Payments.objects.create(
                    user=payment_data["user"],
                    paid_course=payment_data["paid_course"],
                    paid_lesson=payment_data["paid_lesson"],
                    amount=payment_data["amount"],
                    payment_method=payment_data["payment_method"],
                )
                created_count += 1
                self.stdout.write(f"Создан платеж: {payment}")

        self.stdout.write(self.style.SUCCESS(f"Успешно создано {created_count} платежей"))
