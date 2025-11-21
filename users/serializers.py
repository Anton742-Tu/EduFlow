from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User, Payments
from typing import Any, Dict


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для JWT с авторизацией по email"""

    def validate(self, attrs):
        # Используем email вместо username
        authenticate_kwargs = {
            'email': attrs.get('email'),
            'password': attrs.get('password'),
        }

        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)

        if self.user is None or not self.user.is_active:
            raise serializers.ValidationError(
                _('No active account found with the given credentials')
            )

        data = {}
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class PaymentsSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей"""

    class Meta:
        model = Payments
        fields = [
            'id', 'user', 'payment_date', 'paid_course',
            'paid_lesson', 'amount', 'payment_method'
        ]
        read_only_fields = ['id', 'payment_date']


class PublicUserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для публичного просмотра профиля пользователя.
    Доступна только общая информация без чувствительных данных.
    """

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'city', 'avatar',
            'date_joined'
        ]
        read_only_fields = ['id', 'email', 'date_joined']


class PrivateUserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для приватного просмотра собственного профиля.
    Включает все данные пользователя, включая историю платежей.
    """
    payments = PaymentsSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'city', 'avatar', 'date_joined', 'last_login',
            'payments', 'is_active', 'is_staff'
        ]
        read_only_fields = [
            'id', 'email', 'date_joined', 'last_login',
            'is_active', 'is_staff', 'payments'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля пользователя"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'city', 'avatar'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'city', 'avatar', 'password', 'password_confirm'
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user
