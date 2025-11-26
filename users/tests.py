from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Payments, Subscription
from .serializers import PublicUserProfileSerializer, UserCreateSerializer

User = get_user_model()


class UserModelTests(TestCase):
    """
    Тестирование модели пользователя.
    """

    def test_create_user(self) -> None:
        """Тест создания обычного пользователя"""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", first_name="John", last_name="Doe"
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_create_superuser(self) -> None:
        """Тест создания суперпользователя"""
        admin_user = User.objects.create_superuser(email="admin@example.com", password="adminpass123")

        self.assertEqual(admin_user.email, "admin@example.com")
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class PaymentsModelTests(TestCase):
    """
    Тестирование модели платежей.
    """

    def test_payment_creation(self) -> None:
        """Тест создания платежа"""
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        payment = Payments.objects.create(user=user, amount=1000, payment_method="card")

        self.assertEqual(payment.user, user)
        self.assertEqual(payment.amount, 1000)
        self.assertEqual(payment.payment_method, "card")


class SubscriptionModelTests(TestCase):
    """
    Тестирование модели подписки.
    """

    def test_subscription_creation(self) -> None:
        """Тест создания подписки"""
        from materials.models import Course

        user = User.objects.create_user(email="test@example.com", password="testpass123")
        course = Course.objects.create(title="Test Course", owner=user)

        subscription = Subscription.objects.create(user=user, course=course)

        self.assertEqual(subscription.user, user)
        self.assertEqual(subscription.course, course)
        self.assertIsNotNone(subscription.created_at)


class UserSerializerTests(TestCase):
    """
    Тестирование сериализаторов пользователя.
    """

    def test_user_create_serializer_valid_data(self) -> None:
        """Тест валидных данных сериализатора создания пользователя"""
        data = {
            "email": "test@example.com",
            "password": "TestPass123",
            "password_confirm": "TestPass123",
            "first_name": "John",
            "last_name": "Doe",
        }

        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_user_create_serializer_password_mismatch(self) -> None:
        """Тест несовпадающих паролей в сериализаторе"""
        data = {
            "email": "test@example.com",
            "password": "TestPass123",
            "password_confirm": "DifferentPass123",
            "first_name": "John",
            "last_name": "Doe",
        }

        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_public_user_profile_serializer_fields(self) -> None:
        """Тест полей публичного сериализатора профиля"""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", first_name="John", last_name="Doe", city="Moscow"
        )

        serializer = PublicUserProfileSerializer(user)
        data = serializer.data

        # Проверяем что есть только публичные поля
        self.assertIn("id", data)
        self.assertIn("email", data)
        self.assertIn("first_name", data)
        self.assertIn("city", data)
        self.assertIn("date_joined", data)

        # Проверяем что нет приватных полей
        self.assertNotIn("password", data)
        self.assertNotIn("last_name", data)
        self.assertNotIn("payments", data)


class UserViewSetTests(APITestCase):
    """
    Тестирование ViewSet пользователей.
    """

    def setUp(self) -> None:
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")
        self.admin_user = User.objects.create_superuser(email="admin@example.com", password="adminpass123")

    def test_user_registration(self) -> None:
        """Тест регистрации пользователя"""
        data = {
            "email": "newuser@example.com",
            "password": "NewPass123",
            "password_confirm": "NewPass123",
            "first_name": "New",
            "last_name": "User",
        }

        response = self.client.post("/api/users/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email="newuser@example.com").count(), 1)

    def test_get_own_profile(self) -> None:
        """Тест получения собственного профиля"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
