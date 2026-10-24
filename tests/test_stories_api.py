from unittest import mock

import pytest

from apps.stories.models import Story

from .factories import AuthorProfileFactory, GenreFactory, StoryFactory

pytestmark = pytest.mark.django_db


def test_list_shows_only_published_to_anonymous(api_client):
    StoryFactory(status=Story.Status.PUBLISHED)
    StoryFactory(status=Story.Status.DRAFT)

    response = api_client.get("/api/stories/")

    assert response.status_code == 200
    assert response.data["count"] == 1


def test_author_sees_own_draft_but_others_do_not(api_client):
    draft = StoryFactory(status=Story.Status.DRAFT)

    assert api_client.get(f"/api/stories/{draft.pk}/").status_code == 404
    api_client.force_authenticate(draft.author.user)
    assert api_client.get(f"/api/stories/{draft.pk}/").status_code == 200


def test_create_requires_authentication(api_client):
    genre = GenreFactory()
    response = api_client.post("/api/stories/", {"title": "T", "text": "x", "genre": genre.pk})
    assert response.status_code in (401, 403)


def test_create_sets_author_and_draft_status(api_client):
    profile = AuthorProfileFactory()
    genre = GenreFactory()
    api_client.force_authenticate(profile.user)

    response = api_client.post("/api/stories/", {"title": "T", "text": "x", "genre": genre.pk})

    assert response.status_code == 201
    story = Story.objects.get(pk=response.data["id"])
    assert story.author == profile
    assert story.status == Story.Status.DRAFT


def test_only_author_can_update(api_client):
    story = StoryFactory()
    intruder = AuthorProfileFactory().user
    api_client.force_authenticate(intruder)

    response = api_client.patch(f"/api/stories/{story.pk}/", {"title": "Взлом"})

    assert response.status_code == 403


def test_publish_enqueues_task_and_event_after_commit(api_client, django_capture_on_commit_callbacks):
    story = StoryFactory(status=Story.Status.DRAFT)
    api_client.force_authenticate(story.author.user)

    with mock.patch("apps.stories.views.notify_story_published") as task, mock.patch(
        "apps.stories.views.publish_story_published"
    ) as event:
        with django_capture_on_commit_callbacks(execute=True):
            response = api_client.post(f"/api/stories/{story.pk}/publish/")

    assert response.status_code == 200
    story.refresh_from_db()
    assert story.status == Story.Status.PUBLISHED
    assert story.published_at is not None
    task.delay.assert_called_once_with(story.pk)
    event.assert_called_once_with(story.pk, story.author_id)


def test_publish_twice_returns_conflict(api_client):
    story = StoryFactory(status=Story.Status.PUBLISHED)
    api_client.force_authenticate(story.author.user)

    response = api_client.post(f"/api/stories/{story.pk}/publish/")

    assert response.status_code == 409


def test_retrieve_publishes_view_event(api_client):
    story = StoryFactory()

    with mock.patch("apps.stories.views.publish_story_viewed") as event:
        response = api_client.get(f"/api/stories/{story.pk}/")

    assert response.status_code == 200
    event.assert_called_once_with(story.pk, None)
