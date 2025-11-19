from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Payments
from typing import Any, Dict


class PaymentsSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей"""

    class Meta:
        model = Payments
        fields = [
            'id', 'user', 'payment_date', 'paid_course',
            'paid_lesson', 'amount', 'payment_method'
        ]
        read_only_fields = ['id', 'payment_date']


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя с историей платежей"""
    payments = PaymentsSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'city', 'avatar', 'date_joined', 'last_login',
            'payments'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']


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
        return user  # type: ignore
