from django.core.management.base import BaseCommand
from users.tasks import deactivate_inactive_users


class Command(BaseCommand):
    help = 'Manually deactivate users who have not logged in for more than 30 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which users would be deactivated without actually deactivating them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write('🔍 Режим предпросмотра (dry-run)...')

            from datetime import datetime, timedelta
            from django.utils import timezone
            from users.models import User

            month_ago = timezone.now() - timedelta(days=30)
            inactive_users = User.objects.filter(
                last_login__lt=month_ago,
                is_active=True
            ).exclude(is_staff=True).exclude(is_superuser=True)

            self.stdout.write(f'Найдено пользователей для деактивации: {inactive_users.count()}')

            for user in inactive_users:
                self.stdout.write(f'  - {user.email} (last login: {user.last_login})')

        else:
            self.stdout.write('🚀 Запуск деактивации неактивных пользователей...')
            result = deactivate_inactive_users.delay()
            self.stdout.write(self.style.SUCCESS(f'Задача запущена. ID: {result.id}'))