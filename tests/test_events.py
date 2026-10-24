import json

import pytest

from apps.events import producer
from apps.events.consumer import handle_message

from .factories import StoryFactory


def test_publish_is_noop_when_kafka_disabled(settings):
    settings.KAFKA_ENABLED = False
    assert producer.publish_story_viewed(1, None) is False


def test_event_envelope_has_required_fields():
    event = producer.make_event("story.viewed", {"story_id": 7})

    assert set(event) == {"event_id", "type", "occurred_at", "data"}
    assert event["data"] == {"story_id": 7}


@pytest.mark.django_db
def test_consumer_increments_views():
    story = StoryFactory()
    raw = json.dumps({"event_id": "x", "type": "story.viewed", "data": {"story_id": story.pk}})

    handle_message(raw.encode())
    handle_message(raw.encode())

    story.refresh_from_db()
    # TODO(вечер 2): после добавления защиты от дублей по event_id здесь должно быть 1.
    assert story.views_count == 2
