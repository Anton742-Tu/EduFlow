from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User, Payments
from materials.models import Course, Lesson


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми платежами'

    def handle(self, *args, **options):
        # Получаем существующие объекты
        users = User.objects.all()
        courses = Course.objects.all()
        lessons = Lesson.objects.all()

        if not users.exists():
            self.stdout.write(
                self.style.ERROR('Сначала создайте пользователей!')
            )
            return

        if not courses.exists():
            self.stdout.write(
                self.style.ERROR('Сначала создайте курсы!')
            )
            return

        if not lessons.exists():
            self.stdout.write(
                self.style.ERROR('Сначала создайте уроки!')
            )
            return

        # Создаем тестовые платежи
        payments_data = [
            {
                'user': users[0],
                'paid_course': courses[0],
                'paid_lesson': None,
                'amount': 10000.00,
                'payment_method': 'transfer'
            },
            {
                'user': users[0],
                'paid_course': None,
                'paid_lesson': lessons[0],
                'amount': 1500.00,
                'payment_method': 'cash'
            },
        ]

        created_count = 0
        for payment_data in payments_data:
            payment, created = Payments.objects.get_or_create(
                user=payment_data['user'],
                paid_course=payment_data['paid_course'],
                paid_lesson=payment_data['paid_lesson'],
                defaults={
                    'amount': payment_data['amount'],
                    'payment_method': payment_data['payment_method']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создан платеж: {payment}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {created_count} платежей')
        )
