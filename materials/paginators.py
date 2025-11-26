from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from typing import Any, Dict


class StandardResultsSetPagination(PageNumberPagination):
    """
    Стандартный пагинатор для вывода результатов.
    """
    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр для изменения размера страницы
    max_page_size = 100  # Максимальное количество элементов на странице

    def get_paginated_response(self, data: list) -> Response:
        """
        Переопределяем метод для добавления метаданных.
        """
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'results': data
        })


class LargeResultsSetPagination(PageNumberPagination):
    """
    Пагинатор для вывода большего количества элементов на странице.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200

    def get_paginated_response(self, data: list) -> Response:
        """
        Переопределяем метод для добавления метаданных.
        """
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'results': data
        })