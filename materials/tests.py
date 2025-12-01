from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from users.models import Subscription

from .models import Course, Lesson
from .serializers import LessonSerializer
from .validators import YouTubeURLValidator

User = get_user_model()


class YouTubeURLValidatorTests(TestCase):
    """
    Тестирование класса-валидатора YouTubeURLValidator.
    """

    def test_valid_youtube_urls(self) -> None:
        """Тестируем валидные YouTube ссылки"""
        from .validators import YouTubeURLValidator

        validator = YouTubeURLValidator()
        valid_urls = [
            "https://www.youtube.com/watch?v=abc123",
            "https://youtu.be/abc123",
            "https://www.youtube.com/embed/abc123",
            "",  # Пустая строка должна проходить
        ]

        for url in valid_urls:
            # Должно пройти без ошибок
            if url:  # Проверяем что строка не пустая
                validator(url)
            # Пустая строка тоже должна проходить без ошибок

    def test_invalid_youtube_urls(self) -> None:
        """Тестируем невалидные ссылки"""
        from .validators import YouTubeURLValidator

        validator = YouTubeURLValidator()
        invalid_urls = ["https://vimeo.com/123456", "https://example.com/video", "not-a-url"]

        for url in invalid_urls:
            # Должно вызвать ValidationError
            with self.assertRaises(Exception):
                validator(url)


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
    """
    Тестирование валидации YouTube ссылок на уровне модели.
    """

    def test_lesson_with_valid_youtube_url(self) -> None:
        """Создание урока с валидной YouTube ссылкой"""
        user = User.objects.create_user(email="test@test.com", password="testpass123")
        course = Course.objects.create(title="Test Course", owner=user)

        lesson = Lesson(
            title="Valid YouTube Lesson",
            description="Test Description",
            video_url="https://www.youtube.com/watch?v=abc123",
            course=course,
            owner=user,
            order=1,
        )

        # Должно пройти без ошибок
        lesson.full_clean()

    def test_lesson_with_invalid_url_raises_error(self) -> None:
        """Создание урока с невалидной ссылкой вызывает ошибку"""
        user = User.objects.create_user(email="test@test.com", password="testpass123")
        course = Course.objects.create(title="Test Course", owner=user)

        lesson = Lesson(
            title="Invalid URL Lesson",
            description="Test Description",
            video_url="https://vimeo.com/123456",  # Не YouTube
            course=course,
            owner=user,
            order=1,
        )

        # Должно вызвать ValidationError
        with self.assertRaises(Exception):
            lesson.full_clean()


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


class LessonCRUDTestCase(APITestCase):
    """
    Тестирование CRUD операций для уроков с разными правами доступа.
    """

    def setUp(self) -> None:
        """Заполнение базы данных тестовыми данными"""
        # Создаем группу модераторов
        self.moderator_group, created = Group.objects.get_or_create(name="moderators")

        # Создаем пользователей с разными ролями
        self.regular_user = User.objects.create_user(
            email="regular@test.com", password="testpass123", first_name="Regular", last_name="User"
        )

        self.moderator_user = User.objects.create_user(
            email="moderator@test.com", password="testpass123", first_name="Moderator", last_name="User"
        )
        self.moderator_user.groups.add(self.moderator_group)

        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="testpass123", first_name="Admin", last_name="User", is_staff=True
        )

        # Создаем курс
        self.course = Course.objects.create(
            title="Test Course", description="Test Course Description", owner=self.regular_user
        )

        # Создаем уроки
        self.lesson1 = Lesson.objects.create(
            title="Lesson 1", description="Lesson 1 Description", course=self.course, owner=self.regular_user, order=1
        )

        self.lesson2 = Lesson.objects.create(
            title="Lesson 2", description="Lesson 2 Description", course=self.course, owner=self.regular_user, order=2
        )

        # Создаем урок другого пользователя
        self.other_user = User.objects.create_user(email="other@test.com", password="testpass123")

        self.other_lesson = Lesson.objects.create(
            title="Other Lesson",
            description="Other Lesson Description",
            course=self.course,
            owner=self.other_user,
            order=3,
        )

    def test_lesson_retrieve_moderator(self) -> None:
        """Тест получения урока модератором"""
        self.client.force_authenticate(user=self.moderator_user)
        response = self.client.get(f"/api/lessons/{self.lesson1.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Lesson 1")

    def test_lesson_update_owner(self) -> None:
        """Тест обновления урока владельцем"""
        self.client.force_authenticate(user=self.regular_user)

        update_data = {
            "title": "Updated Lesson 1",
            "description": "Updated Description",
            "course": self.course.id,
            "order": 1,
        }

        # Используем PUT на детальный эндпоинт урока
        response = self.client.put(f"/api/lessons/{self.lesson1.id}/", update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем обновление в базе
        self.lesson1.refresh_from_db()
        self.assertEqual(self.lesson1.title, "Updated Lesson 1")

    def test_lesson_update_moderator(self) -> None:
        """Тест обновления урока модератором"""
        self.client.force_authenticate(user=self.moderator_user)

        update_data = {
            "title": "Moderator Updated",
            "description": "Moderator Updated Description",
            "course": self.course.id,
            "order": 1,
        }

        response = self.client.put(f"/api/lessons/{self.lesson1.id}/", update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.lesson1.refresh_from_db()
        self.assertEqual(self.lesson1.title, "Moderator Updated")

    def test_lesson_update_other_user_denied(self) -> None:
        """Тест запрета обновления чужого урока"""
        self.client.force_authenticate(user=self.other_user)

        update_data = {
            "title": "Unauthorized Update",
            "description": "Should not work",
            "course": self.course.id,
            "order": 1,
        }

        response = self.client.put(f"/api/lessons/{self.lesson1.id}/", update_data)
        # Должен быть 403 или 404 в зависимости от реализации
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_lesson_delete_owner(self) -> None:
        """Тест удаления урока владельцем"""
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.delete(f"/api/lessons/{self.lesson1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что урок удален
        with self.assertRaises(Lesson.DoesNotExist):
            Lesson.objects.get(id=self.lesson1.id)

    def test_lesson_delete_moderator_denied(self) -> None:
        """Тест запрета удаления урока модератором"""
        self.client.force_authenticate(user=self.moderator_user)

        response = self.client.delete(f"/api/lessons/{self.lesson1.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_delete_admin(self) -> None:
        """Тест удаления урока администратором"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(f"/api/lessons/{self.lesson1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SubscriptionTestCase(APITestCase):
    """
    Тестирование функционала подписки на обновления курса.
    """

    def setUp(self) -> None:
        """Заполнение базы данных тестовыми данными"""
        self.user = User.objects.create_user(email="user@test.com", password="testpass123")

        self.course = Course.objects.create(
            title="Test Course for Subscription", description="Test Course Description", owner=self.user
        )

    def test_subscribe_to_course(self) -> None:
        """Тест подписки на курс"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(f"/api/courses/{self.course.id}/subscribe/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка оформлена")

        # Проверяем, что подписка создана в базе
        subscription = Subscription.objects.get(user=self.user, course=self.course)
        self.assertIsNotNone(subscription)

    def test_unsubscribe_from_course(self) -> None:
        """Тест отписки от курса"""
        # Сначала создаем подписку
        Subscription.objects.create(user=self.user, course=self.course)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/courses/{self.course.id}/unsubscribe/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка отменена")

        # Проверяем, что подписка удалена
        with self.assertRaises(Subscription.DoesNotExist):
            Subscription.objects.get(user=self.user, course=self.course)

    def test_subscribe_twice(self) -> None:
        """Тест повторной подписки (должна быть идемпотентной)"""
        self.client.force_authenticate(user=self.user)

        # Первая подписка
        response1 = self.client.post(f"/api/courses/{self.course.id}/subscribe/")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertTrue(response1.data["created"])  # Первый раз создана

        # Вторая подписка
        response2 = self.client.post(f"/api/courses/{self.course.id}/subscribe/")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data["created"])  # Второй раз не создана

        # Должна быть только одна подписка
        subscriptions_count = Subscription.objects.filter(user=self.user, course=self.course).count()
        self.assertEqual(subscriptions_count, 1)

    def test_subscribe_unauthorized(self) -> None:
        """Тест подписки без авторизации"""
        response = self.client.post(f"/api/courses/{self.course.id}/subscribe/")

        # Может возвращать 401 или 403 в зависимости от настроек
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class LessonSerializerTestCase(TestCase):
    """
    Тестирование сериализатора уроков.
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(email="serializer@test.com", password="testpass123")

        self.course = Course.objects.create(
            title="Serializer Course", description="Serializer Course Description", owner=self.user
        )

        self.lesson_data = {
            "title": "Serializer Lesson",
            "description": "Serializer Lesson Description",
            "course": self.course.id,
            "order": 1,
            "owner": self.user.id,
        }

    def test_lesson_serializer_valid_data(self) -> None:
        """Тест валидных данных сериализатора"""
        serializer = LessonSerializer(data=self.lesson_data)
        self.assertTrue(serializer.is_valid())

    def test_lesson_serializer_missing_title(self) -> None:
        """Тест отсутствия обязательного поля title"""
        invalid_data = self.lesson_data.copy()
        invalid_data.pop("title")

        serializer = LessonSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
