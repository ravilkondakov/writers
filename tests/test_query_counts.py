import pytest

from .factories import ReviewFactory, StoryFactory

pytestmark = pytest.mark.django_db


@pytest.mark.xfail(
    strict=True,
    reason="TODO(вечер 1): N+1 в списке рассказов. Исправьте и удалите этот маркер.",
)
def test_story_list_does_not_have_n_plus_one(api_client, django_assert_max_num_queries):
    for _ in range(10):
        story = StoryFactory()
        ReviewFactory(story=story)

    # COUNT для пагинации + сам список (с join на author и genre и подсчётом рейтинга) = 2 запроса.
    # Допускаем запас до 4.
    with django_assert_max_num_queries(4):
        response = api_client.get("/api/stories/")

    assert response.status_code == 200
