from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "created_at", "updated_at", "lessons_count")
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")

    def lessons_count(self, obj: Course) -> int:
        """Возвращает количество уроков в курсе"""
        count: int = obj.lessons.count()
        return count

    # Выносим установку атрибута за пределы функции
    lessons_count.short_description = "Количество уроков"  # type: ignore[attr-defined]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "owner", "created_at")
    list_filter = ("course", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("course", "order")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Lesson]:
        """Оптимизация запроса с использованием select_related"""
        queryset: QuerySet[Lesson] = super().get_queryset(request)
        return queryset.select_related("course", "owner")
