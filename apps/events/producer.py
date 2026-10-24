"""Публикация событий предметной области в Kafka.

Формат события (конверт): event_id, type, occurred_at, data.
event_id нужен потребителям для защиты от дублей (Kafka гарантирует
доставку «минимум один раз», значит, дубли возможны).

Ограничение текущей версии: если Kafka недоступна, событие теряется (мы только пишем в лог).
Правильное решение называется transactional outbox: событие сначала пишется в таблицу
в той же транзакции, что и данные, а отдельный процесс отправляет его в Kafka.
Это задача уровня «после собеседования».
"""
import json
import logging
import uuid

from django.conf import settings
from django.utils import timezone

from . import topics

logger = logging.getLogger(__name__)

_producer = None


def _get_producer():
    global _producer
    if _producer is None:
        from confluent_kafka import Producer

        _producer = Producer(
            {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "enable.idempotence": True,
                "acks": "all",
            }
        )
    return _producer


def _on_delivery(err, msg):
    if err is not None:
        logger.error("Kafka delivery failed: %s", err)


def make_event(event_type: str, data: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "occurred_at": timezone.now().isoformat(),
        "data": data,
    }


def publish(topic: str, key, event: dict) -> bool:
    """Отправляет событие. Возвращает True, если оно передано продюсеру."""
    if not settings.KAFKA_ENABLED:
        logger.debug("Kafka disabled, skip event %s", event["type"])
        return False
    try:
        producer = _get_producer()
        producer.produce(
            topic,
            key=str(key),  # один ключ = одна партиция = сохраняется порядок событий по ключу
            value=json.dumps(event).encode(),
            on_delivery=_on_delivery,
        )
        producer.poll(0)
        return True
    except Exception:
        logger.exception("Failed to publish event %s", event["type"])
        return False


def publish_story_viewed(story_id: int, user_id: int | None) -> bool:
    event = make_event(topics.STORY_VIEWED, {"story_id": story_id, "user_id": user_id})
    return publish(topics.STORY_VIEWED, story_id, event)


def publish_story_published(story_id: int, author_id: int) -> bool:
    event = make_event(topics.STORY_PUBLISHED, {"story_id": story_id, "author_id": author_id})
    return publish(topics.STORY_PUBLISHED, story_id, event)
