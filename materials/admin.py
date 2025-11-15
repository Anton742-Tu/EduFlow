from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'updated_at', 'lessons_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def lessons_count(self, obj):
        return obj.lessons.count()

    lessons_count.short_description = _('Lessons count')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'owner', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('course', 'order')