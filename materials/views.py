from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import api_view
from rest_framework.response import Response

def home(request):
    return HttpResponse(
        "<h1>EduFlow - Образовательная платформа</h1>"
        "<p>Добро пожаловать в EduFlow! Платформа для создания и прохождения курсов.</p>"
        "<p><a href='/admin/'>Перейти в админку</a></p>"
        "<p><a href='/api/test/'>Тестовый API</a></p>"
    )

@api_view(['GET'])
def test_api(request):
    """Простой тестовый API endpoint"""
    return Response({
        'message': 'EduFlow API работает!',
        'status': 'success',
        'version': '1.0'
    })