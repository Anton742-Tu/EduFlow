from typing import Any, Dict

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from materials.models import Course

from .models import Payments, Subscription, User  # Добавляем Subscription


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для JWT с авторизацией по email"""

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, str]:
        print(f"🔧 JWT Auth attempt: {attrs.get('email')}")

        # Упрощенная версия - используем стандартную логику
        try:
            data = super().validate(attrs)
            print(f"✅ JWT Auth successful for: {self.user.email}")
            return data
        except Exception as e:
            print(f"❌ JWT Auth failed: {e}")
            raise


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class PaymentsSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей"""

    class Meta:
        model = Payments
        fields = [
            "id",
            "user",
            "payment_date",
            "paid_course",
            "paid_lesson",
            "amount",
            "payment_method",
            "payment_status",
            "stripe_payment_intent_id",
            "stripe_session_id",
        ]
        read_only_fields = ["id", "payment_date"]


class SubscriptionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    subscribed_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "user", "course", "course_title", "subscribed_at"]
        read_only_fields = ["id", "user", "course_title", "subscribed_at"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Проверяем, что пользователь не подписан дважды на один курс"""
        user = self.context["request"].user
        course = attrs["course"]

        if Subscription.objects.filter(user=user, course=course).exists():
            raise serializers.ValidationError("Вы уже подписаны на этот курс")

        return attrs


class PublicUserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для публичного просмотра профиля пользователя.
    Доступна только общая информация без чувствительных данных.
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "city", "avatar", "date_joined"]
        read_only_fields = ["id", "email", "date_joined"]


class PrivateUserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для приватного просмотра собственного профиля.
    Включает все данные пользователя, включая историю платежей.
    """

    payments = PaymentsSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "date_joined",
            "last_login",
            "payments",
            "is_active",
            "is_staff",
        ]
        read_only_fields = ["id", "email", "date_joined", "last_login", "is_active", "is_staff", "payments"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля пользователя"""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "city", "avatar"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "city", "avatar", "password", "password_confirm"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        # Создаем пользователя без пароля
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            city=validated_data.get('city', ''),
            avatar=validated_data.get('avatar')
        )

        # Устанавливаем пароль отдельно
        user.set_password(password)
        user.save()
        return user


class CoursePaymentSerializer(serializers.Serializer):
    """
    Сериализатор для создания платежа за курс
    """

    course_id = serializers.IntegerField()

    def validate_course_id(self, value: int) -> int:
        try:
            course = Course.objects.get(id=value)
            if not hasattr(course, "price") or not course.price:
                raise serializers.ValidationError("Курс не имеет установленной цены")
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Курс не найден")


class PaymentSessionSerializer(serializers.Serializer):
    """
    Сериализатор ответа с сессией оплаты
    """

    session_id = serializers.CharField()
    url = serializers.URLField()
