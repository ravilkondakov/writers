"""Фоновые задачи (Celery, брокер RabbitMQ)."""
import logging

from celery import shared_task

from .models import Story

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,  # паузы между попытками растут: 1, 2, 4... секунды
    retry_jitter=True,
    max_retries=3,
)
def notify_story_published(self, story_id: int) -> None:
    """Уведомляет подписчиков о новом рассказе (пока только пишет в лог).

    TODO(вечер 2):
     1. Идемпотентность: если задачу выполнят дважды (а так бывает), дубль уведомления
        не должен уйти. Как это проверить? Подсказка: таблица Notification с unique
        (story, recipient) или ключ в Redis.
     2. Отдельная очередь: настройте CELERY_TASK_ROUTES, запустите воркер с `-Q notifications`
        и найдите эту очередь в веб-интерфейсе RabbitMQ (localhost:15672).
     3. Dead-letter: что происходит с задачей после max_retries? Куда её положить?
    """
    story = Story.objects.select_related("author").get(pk=story_id)
    logger.info("Notify subscribers: story=%s author=%s", story.pk, story.author.pen_name)
