from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from typing import Any


class Course(models.Model):
    """Модель курса"""
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('Enter the course title')
    )
    preview = models.ImageField(
        _('preview image'),
        upload_to='courses/previews/',
        blank=True,
        null=True,
        help_text=_('Upload a course preview image')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Enter the course description')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses',
        verbose_name=_('owner')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return str(self.title)  # ← Явное преобразование в str


class Lesson(models.Model):
    """Модель урока"""
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('Enter the lesson title')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Enter the lesson description')
    )
    preview = models.ImageField(
        _('preview image'),
        upload_to='lessons/previews/',
        blank=True,
        null=True,
        help_text=_('Upload a lesson preview image')
    )
    video_url = models.URLField(
        _('video URL'),
        blank=True,
        help_text=_('Enter the video URL for this lesson')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('course'),
        help_text=_('Select the course for this lesson')
    )
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
        help_text=_('Lesson order in the course')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lessons',
        verbose_name=_('owner')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('lesson')
        verbose_name_plural = _('lessons')
        ordering = ['course', 'order', 'created_at']

    def __str__(self) -> str:
        course_title = str(self.course.title) if self.course else "No Course"
        return f"{course_title} - {self.title}"  # ← Явное преобразование

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Автоматически устанавливаем порядок, если не указан"""
        if self.order == 0:
            # Находим максимальный порядок в курсе и добавляем 1
            last_lesson = Lesson.objects.filter(course=self.course).order_by('-order').first()
            self.order = last_lesson.order + 1 if last_lesson else 1
        super().save(*args, **kwargs)