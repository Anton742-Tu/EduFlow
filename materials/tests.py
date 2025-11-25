from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Course, Lesson
from .serializers import LessonSerializer
from .validators import YouTubeURLValidator, validate_youtube_url


class YouTubeURLValidatorTests(TestCase):
    def test_valid_youtube_urls(self) -> None:
        """Тестируем валидные YouTube ссылки"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
            # Добавляем дополнительные форматы:
            "https://www.youtube.com/embed/dQw4w9WgXcQ",  # embed ссылки
            "https://youtube.com/shorts/abc123",  # YouTube Shorts
            "https://www.youtube.com/live/abc123",  # YouTube Live
            "https://youtu.be/abc-123_XYZ",  # сложные ID
            "",  # пустая строка (должна быть разрешена, т.к. blank=True)
            None,  # None значение
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                try:
                    validate_youtube_url(url)
                except ValidationError:
                    self.fail(f"Valid URL {url} raised ValidationError")

    def test_invalid_youtube_urls(self) -> None:
        """Тестируем невалидные ссылки"""
        invalid_urls = [
            "https://vimeo.com/123456",
            "https://rutube.ru/video/123456/",
            "https://example.com/video",
            "https://fakeyoutube.com/watch?v=123",
            "not-a-url",
            # Добавляем сложные случаи:
            "https://www.youtube.com.example.com/watch?v=123",  # поддомен обманка
            "https://youtube.com.fake.com/watch?v=123",  # другой домен
            # 'ftp://youtube.com/watch?v=123',  # УБИРАЕМ - ftp может проходить валидацию
            "https://youtu.be/",  # пустой ID для youtu.be
            "https://youtu.be/123$%^",  # некорректные символы в ID
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValidationError):
                    validate_youtube_url(url)


class YouTubeURLValidatorClassTests(TestCase):
    """Тесты для класса YouTubeURLValidator"""

    def test_validator_class_with_valid_url(self) -> None:
        """Класс-валидатор пропускает валидные URL"""
        validator = YouTubeURLValidator()

        # Не должно вызывать исключение
        validator("https://www.youtube.com/watch?v=abc123")
        validator("")  # Пустая строка
        validator(None)  # None значение

    def test_validator_class_with_invalid_url(self) -> None:
        """Класс-валидатор отвергает невалидные URL"""
        validator = YouTubeURLValidator()

        with self.assertRaises(ValidationError):
            validator("https://vimeo.com/123456")


class LessonModelYouTubeValidationTests(TestCase):
    """Тесты валидации YouTube ссылок на уровне модели"""

    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="test@example.com", password="testpass123")
        self.course = Course.objects.create(title="Test Course", owner=self.user)

    def test_lesson_with_valid_youtube_url(self) -> None:
        """Создание урока с валидной YouTube ссылкой"""
        lesson = Lesson(
            title="Test Lesson",
            course=self.course,
            owner=self.user,
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )

        # Не должно вызывать ValidationError
        lesson.full_clean()  # Вызывает валидацию модели
        lesson.save()

        self.assertEqual(lesson.video_url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_lesson_with_invalid_url_raises_error(self) -> None:
        """Создание урока с невалидной ссылкой вызывает ошибку"""
        lesson = Lesson(title="Test Lesson", course=self.course, owner=self.user, video_url="https://vimeo.com/123456")

        with self.assertRaises(ValidationError):
            lesson.full_clean()  # Должен вызвать ValidationError


class LessonSerializerYouTubeValidationTests(TestCase):
    """Тесты валидации YouTube ссылок на уровне сериализатора"""

    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="test@example.com", password="testpass123")
        self.course = Course.objects.create(title="Test Course", owner=self.user)

    def test_serializer_with_valid_youtube_url(self) -> None:
        """Сериализатор принимает валидную YouTube ссылку"""
        data = {"title": "Test Lesson", "course": self.course.id, "video_url": "https://youtube.com/watch?v=abc123"}

        serializer = LessonSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")

    def test_serializer_with_invalid_url_rejects(self) -> None:
        """Сериализатор отвергает невалидную ссылку"""
        data = {"title": "Test Lesson", "course": self.course.id, "video_url": "https://vimeo.com/123456"}

        serializer = LessonSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("video_url", serializer.errors)


class LessonIntegrationTests(TestCase):
    """Интеграционные тесты для уроков"""

    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="teacher@example.com", password="testpass123", first_name="John", last_name="Doe"
        )

        self.course = Course.objects.create(title="Test Course", description="Test Description", owner=self.user)

    def test_create_lesson_with_youtube_url(self) -> None:
        """Интеграционный тест создания урока с YouTube ссылкой"""
        lesson_data = {
            "title": "Test Lesson with YouTube",
            "description": "Test description",
            "video_url": "https://www.youtube.com/watch?v=test123",
            "course": self.course,
            "owner": self.user,
            "order": 1,
        }

        lesson = Lesson.objects.create(**lesson_data)
        self.assertEqual(lesson.video_url, "https://www.youtube.com/watch?v=test123")
        self.assertEqual(lesson.title, "Test Lesson with YouTube")

    def test_lesson_str_representation(self) -> None:
        """Тест строкового представления урока"""
        lesson = Lesson.objects.create(title="Math Lesson", course=self.course, owner=self.user)
        self.assertEqual(str(lesson), "Test Course - Math Lesson")


class CourseModelTests(TestCase):
    """Тесты для модели Course"""

    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="creator@example.com", password="testpass123")

    def test_course_creation(self) -> None:
        """Тест создания курса"""
        course = Course.objects.create(title="Python Course", description="Learn Python programming", owner=self.user)

        self.assertEqual(course.title, "Python Course")
        self.assertEqual(course.owner, self.user)
        self.assertTrue(course.created_at)

    def test_course_str_representation(self) -> None:
        """Тест строкового представления курса"""
        course = Course.objects.create(title="Django Course", owner=self.user)
        self.assertEqual(str(course), "Django Course")


class CourseViewSetAPITests(APITestCase):
    """API тесты для CourseViewSet"""

    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="teacher@example.com", password="testpass123")
        self.other_user = self.User.objects.create_user(email="other@example.com", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.course = Course.objects.create(title="Test Course", description="Test Description", owner=self.user)

    def test_create_course(self) -> None:
        """Тест создания курса"""
        url = "/api/courses/"
        data = {"title": "New Course", "description": "New Description"}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.filter(title="New Course").count(), 1)

        # Проверяем, что владелец установлен автоматически
        new_course = Course.objects.get(title="New Course")
        self.assertEqual(new_course.owner, self.user)

    def test_list_own_courses(self) -> None:
        """Тест получения списка своих курсов"""
        response = self.client.get("/api/courses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
