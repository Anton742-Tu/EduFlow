import os
from typing import Any

from celery import Celery

# Установка переменной окружения для настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduflow.settings")

app = Celery("eduflow")

# Использование строки конфигурации из настроек Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Настройки для Windows
app.conf.update(
    worker_pool="solo",  # Используем solo pool вместо prefork для Windows
    task_always_eager=False,
)

# Автоматическое обнаружение задач из приложений
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self: Any) -> None:
    print(f"Request: {self.request!r}")
