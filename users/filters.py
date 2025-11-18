from django_filters import rest_framework as filters
from .models import Payments


class PaymentsFilter(filters.FilterSet):
    """Фильтр для платежей"""

    # Фильтрация по курсу или уроку
    course = filters.NumberFilter(field_name='paid_course__id', label='ID курса')
    lesson = filters.NumberFilter(field_name='paid_lesson__id', label='ID урока')

    # Фильтрация по способу оплаты
    payment_method = filters.ChoiceFilter(
        choices=Payments.PaymentMethod.choices,
        label='Способ оплаты'
    )

    # Фильтрация по дате (дополнительно)
    payment_date_after = filters.DateTimeFilter(
        field_name='payment_date',
        lookup_expr='gte',
        label='Дата оплаты после'
    )
    payment_date_before = filters.DateTimeFilter(
        field_name='payment_date',
        lookup_expr='lte',
        label='Дата оплаты до'
    )

    class Meta:
        model = Payments
        fields = [
            'course', 'lesson', 'payment_method',
            'payment_date_after', 'payment_date_before'
        ]
