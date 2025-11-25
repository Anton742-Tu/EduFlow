from rest_framework import serializers

from .models import Course, Lesson
from .validators import validate_youtube_url  # Импортируем функцию-валидатор


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уроков с валидацией видео-ссылок
    """

    # Используем функцию-валидатор на уровне поля
    video_url = serializers.URLField(required=False, allow_blank=True, validators=[validate_youtube_url])

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "video_url", "course", "order", "owner", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]
        # УБИРАЕМ валидатор из Meta - он дублируется


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курса"""

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()  # Добавляем поле подписки

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "preview",
            "description",
            "owner",
            "lessons_count",
            "lessons",
            "is_subscribed",  # Добавляем поле
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_lessons_count(self, obj: Course) -> int:
        """Метод для получения количества уроков в курсе"""
        return obj.lessons.count()

    def get_is_subscribed(self, obj: Course) -> bool:
        """Метод для проверки подписки текущего пользователя на курс"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # Импортируем здесь чтобы избежать circular import
            from users.models import Subscription

            return Subscription.objects.filter(user=request.user, course=obj).exists()
        return False
