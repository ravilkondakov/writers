"""Потребитель событий: считает просмотры рассказов.

Работает отдельным процессом (сервис `consumer` в docker-compose).
Масштабирование: запустите несколько копий с одним group.id, и Kafka разделит
партиции между ними.

TODO(вечер 2), от простого к сложному:
 1. Сейчас каждое сообщение = один UPDATE и один commit. Накапливайте пачку
    (например, 100 сообщений или 1 секунда) и делайте один UPDATE на каждый story_id.
 2. Защита от дублей: храните обработанные event_id (таблица или Redis SET) и пропускайте повторы.
 3. «Ядовитые» сообщения (битый JSON): сейчас они уронят процесс. Отправляйте их в топик *.dlq.
"""
import json
import logging

from django.conf import settings
from django.db.models import F

from apps.stories.models import Story

from . import topics

logger = logging.getLogger(__name__)

GROUP_ID = "story-views"


def handle_message(raw: bytes) -> None:
    event = json.loads(raw)
    story_id = event["data"]["story_id"]
    Story.objects.filter(pk=story_id).update(views_count=F("views_count") + 1)


def run_view_counter() -> None:
    from confluent_kafka import Consumer, KafkaError

    consumer = Consumer(
        {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": GROUP_ID,
            "enable.auto.commit": False,  # коммитим сами, после обработки
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([topics.STORY_VIEWED])
    logger.info("Consumer started, group=%s topic=%s", GROUP_ID, topics.STORY_VIEWED)
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.warning("Kafka error: %s", msg.error())
                continue
            handle_message(msg.value())
            consumer.commit(message=msg)
    finally:
        consumer.close()
