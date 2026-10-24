import pytest

from apps.stories.models import Story

from .factories import ReviewFactory, StoryFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_create_review(api_client):
    story = StoryFactory()
    user = UserFactory()
    api_client.force_authenticate(user)

    response = api_client.post("/api/reviews/", {"story": story.pk, "rating": 4, "text": "ok"})

    assert response.status_code == 201
    assert response.data["username"] == user.username


def test_duplicate_review_rejected(api_client):
    review = ReviewFactory()
    api_client.force_authenticate(review.user)

    response = api_client.post("/api/reviews/", {"story": review.story_id, "rating": 3})

    assert response.status_code == 400


@pytest.mark.parametrize("rating", [0, 6, -1])
def test_rating_out_of_range_rejected(api_client, rating):
    story = StoryFactory()
    api_client.force_authenticate(UserFactory())

    response = api_client.post("/api/reviews/", {"story": story.pk, "rating": rating})

    assert response.status_code == 400


def test_cannot_review_draft(api_client):
    story = StoryFactory(status=Story.Status.DRAFT)
    api_client.force_authenticate(UserFactory())

    response = api_client.post("/api/reviews/", {"story": story.pk, "rating": 5})

    assert response.status_code == 400


def test_cannot_review_own_story(api_client):
    story = StoryFactory()
    api_client.force_authenticate(story.author.user)

    response = api_client.post("/api/reviews/", {"story": story.pk, "rating": 5})

    assert response.status_code == 400


def test_only_owner_can_delete(api_client):
    review = ReviewFactory()
    api_client.force_authenticate(UserFactory())

    assert api_client.delete(f"/api/reviews/{review.pk}/").status_code == 403
