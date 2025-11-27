from typing import Any, Optional

from django.core.exceptions import ValidationError


def validate_youtube_url(value: Optional[str]) -> None:
    """
    Валидатор для проверки, что ссылка ведет на YouTube.
    """
    if value and "youtube.com" not in value and "youtu.be" not in value:
        raise ValidationError("Разрешены только ссылки на YouTube")


class YouTubeURLValidator:
    """
    Класс-валидатор для YouTube ссылок.
    """

    def __call__(self, value: Optional[str]) -> None:
        """
        Вызов валидатора.
        """
        validate_youtube_url(value)

    def __eq__(self, other: Any) -> bool:
        """
        Метод для сравнения валидаторов.
        """
        return isinstance(other, YouTubeURLValidator)
