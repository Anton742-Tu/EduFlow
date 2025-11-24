from rest_framework import serializers
from .validators import YouTubeURLValidator, validate_youtube_url
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уроков с валидацией видео-ссылок
    """
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'video_url',
            'course', 'order', 'owner', 'created_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at']
        validators = [
            YouTubeURLValidator(field='video_url')
        ]

    # Альтернативный вариант с функцией-валидатором:
    # video_url = serializers.URLField(
    #     required=False,
    #     allow_blank=True,
    #     validators=[validate_youtube_url]
    # )


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курса"""

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


    def get_lessons_count(self, obj: Course) -> int:
        """Метод для получения количества уроков в курсе"""
        count = obj.lessons.count()
        return int(count)  # ← Явное преобразование в int
