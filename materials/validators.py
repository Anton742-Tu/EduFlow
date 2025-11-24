from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from urllib.parse import urlparse
import re


class YouTubeURLValidator:
    """
    Валидатор для проверки, что ссылка ведет только на youtube.com
    """

    def __init__(self, field='video_url'):
        self.field = field

    def __call__(self, value):
        if value:
            if not self.is_valid_youtube_url(value):
                raise ValidationError(
                    _('Разрешены только ссылки на YouTube (youtube.com).'),
                    code='invalid_url'
                )

    def is_valid_youtube_url(self, url: str) -> bool:
        """
        Проверяет, является ли ссылка валидным YouTube URL
        """
        try:
            parsed_url = urlparse(url)

            # Проверяем домен
            allowed_domains = [
                'youtube.com',
                'www.youtube.com',
                'm.youtube.com',
                'youtu.be'
            ]

            if parsed_url.netloc not in allowed_domains:
                return False

            # Дополнительная проверка для youtu.be (короткие ссылки)
            if parsed_url.netloc == 'youtu.be':
                return bool(re.match(r'^/[a-zA-Z0-9_-]+$', parsed_url.path))

            return True

        except Exception:
            return False


def validate_youtube_url(value: str) -> None:
    """
    Функция-валидатор для проверки YouTube ссылок
    """
    if value:
        validator = YouTubeURLValidator()
        if not validator.is_valid_youtube_url(value):
            raise ValidationError(
                _('Разрешены только ссылки на YouTube (youtube.com).'),
                code='invalid_url'
            )
