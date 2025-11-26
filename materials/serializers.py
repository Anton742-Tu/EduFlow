from typing import Any, Dict

from rest_framework import serializers

from .models import Course, Lesson


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для курсов.
    """

    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "description", "owner", "created_at", "updated_at", "lessons_count", "is_subscribed"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_lessons_count(self, obj: Course) -> int:
        """
        Возвращает количество уроков в курсе.
        """
        count: int = obj.lessons.count()
        return count

    def get_is_subscribed(self, obj: Course) -> bool:
        """
        Проверяет, подписан ли текущий пользователь на курс.
        """
        user = self.context["request"].user
        if user.is_authenticated:
            from users.models import Subscription

            is_subscribed: bool = Subscription.objects.filter(user=user, course=obj).exists()
            return is_subscribed
        return False


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уроков.
    """

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "video_url", "course", "order", "owner", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]

    def validate_video_url(self, value: str) -> str:
        """
        Валидация YouTube ссылки.
        """
        if value and "youtube.com" not in value and "youtu.be" not in value:
            raise serializers.ValidationError("Разрешены только ссылки на YouTube")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Lesson:
        """
        Создание урока с автоматическим назначением владельца.
        """
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
