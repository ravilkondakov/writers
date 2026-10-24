from datetime import timedelta

import pytest
from django.utils import timezone

from apps.stories import selectors

from .factories import GenreFactory, ReviewFactory, StoryFactory

pytestmark = pytest.mark.django_db


def test_top_orders_by_avg_rating_then_count():
    best = StoryFactory(title="best")
    popular = StoryFactory(title="popular")
    ReviewFactory(story=best, rating=5)
    ReviewFactory(story=popular, rating=4)
    ReviewFactory(story=popular, rating=4)

    result = selectors.top_stories()

    assert [r["title"] for r in result] == ["best", "popular"]
    assert result[1]["reviews_count"] == 2


def test_top_ignores_old_reviews_and_other_genres():
    genre = GenreFactory(slug="horror")
    in_genre = StoryFactory(genre=genre)
    other = StoryFactory()
    ReviewFactory(story=in_genre, rating=5)
    ReviewFactory(story=other, rating=5)
    old = ReviewFactory(story=in_genre, rating=1)
    old.created_at = timezone.now() - timedelta(days=30)
    old.save()

    result = selectors.top_stories(genre_slug="horror", days=7)

    assert [r["story_id"] for r in result] == [in_genre.pk]
    assert result[0]["avg_rating"] == 5


def test_top_endpoint(api_client):
    ReviewFactory(rating=4)

    response = api_client.get("/api/stories/top/?days=7&limit=5")

    assert response.status_code == 200
    assert len(response.data) == 1


def test_top_endpoint_validates_params(api_client):
    assert api_client.get("/api/stories/top/?days=abc").status_code == 400
