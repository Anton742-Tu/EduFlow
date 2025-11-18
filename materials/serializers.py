from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для урока"""

    class Meta:
        model = Lesson
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курса"""
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'preview', 'description', 'owner',
            'lessons_count', 'lessons',
            'created_at', 'updated_at'
        ]

    def get_lessons_count(self, obj):
        """Метод для получения количества уроков в курсе"""
        return obj.lessons.count()
