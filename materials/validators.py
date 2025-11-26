import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class YouTubeURLValidator:
    """
    Валидатор для проверки, что ссылка ведет только на youtube.com
    """

    def __init__(self, field="video_url"):
        self.field = field

    def __call__(self, value: str) -> None:
        # Разрешаем пустые значения и None
        if not value:
            return

        if not self.is_valid_youtube_url(value):
            raise ValidationError(_("Разрешены только ссылки на YouTube (youtube.com)."), code="invalid_url")

    def is_valid_youtube_url(self, url: str) -> bool:
        """
        Проверяет, является ли ссылка валидным YouTube URL
        """
        try:
            # Если URL пустой или None - разрешаем
            if not url:
                return True

            parsed_url = urlparse(url)

            # Проверяем домен (приводим к нижнему регистру)
            allowed_domains = ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"]

            domain = parsed_url.netloc.lower()
            if domain not in allowed_domains:
                return False

            # Дополнительная проверка для youtu.be (короткие ссылки)
            if domain == "youtu.be":
                return bool(re.match(r"^/[a-zA-Z0-9_-]+$", parsed_url.path))

            return True

        except Exception:
            return False


def validate_youtube_url(value: str) -> None:
    """
    Валидатор для проверки, что ссылка ведет на YouTube.
    """
    if value and "youtube.com" not in value and "youtu.be" not in value:
        raise ValidationError("Разрешены только ссылки на YouTube")
