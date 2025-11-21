from typing import Any

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from materials.models import Course, Lesson


class Command(BaseCommand):
    help = "Создает группу модераторов с ограниченными правами"

    def handle(self, *args: Any, **options: Any) -> None:
        # Создаем или получаем группу модераторов
        moderators_group, created = Group.objects.get_or_create(name="moderators")

        if created:
            self.stdout.write(self.style.SUCCESS("Группа модераторов создана"))
        else:
            self.stdout.write(self.style.WARNING("Группа модераторов уже существует"))

        # Получаем разрешения для моделей Course и Lesson
        course_content_type = ContentType.objects.get_for_model(Course)
        lesson_content_type = ContentType.objects.get_for_model(Lesson)

        # Разрешения для просмотра (view)
        view_course_permission = Permission.objects.get(codename="view_course", content_type=course_content_type)
        view_lesson_permission = Permission.objects.get(codename="view_lesson", content_type=lesson_content_type)

        # Разрешения для изменения (change)
        change_course_permission = Permission.objects.get(codename="change_course", content_type=course_content_type)
        change_lesson_permission = Permission.objects.get(codename="change_lesson", content_type=lesson_content_type)

        # Добавляем разрешения в группу (только просмотр и изменение)
        moderators_group.permissions.add(
            view_course_permission,
            view_lesson_permission,
            change_course_permission,
            change_lesson_permission,
        )

        # Явно убираем разрешения на создание и удаление
        delete_course_permission = Permission.objects.get(codename="delete_course", content_type=course_content_type)
        delete_lesson_permission = Permission.objects.get(codename="delete_lesson", content_type=lesson_content_type)
        add_course_permission = Permission.objects.get(codename="add_course", content_type=course_content_type)
        add_lesson_permission = Permission.objects.get(codename="add_lesson", content_type=lesson_content_type)

        moderators_group.permissions.remove(
            delete_course_permission,
            delete_lesson_permission,
            add_course_permission,
            add_lesson_permission,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Группе модераторов назначены права: просмотр и изменение курсов/уроков")
        )
        self.stdout.write(self.style.WARNING(f"Группе модераторов запрещены: создание и удаление курсов/уроков"))
