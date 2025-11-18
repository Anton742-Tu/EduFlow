from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User
from .models import User, Payments


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "city", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "city")
    search_fields = ("email", "first_name", "last_name", "city")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "city", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "is_staff", "is_active")}),
    )


@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_date', 'paid_course', 'paid_lesson', 'amount', 'payment_method')
    list_filter = ('payment_date', 'payment_method')
    search_fields = ('user__email', 'paid_course__title', 'paid_lesson__title')
    date_hierarchy = 'payment_date'