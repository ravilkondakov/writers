"""Чтение данных: сложные запросы живут здесь, а не во views.

Selectors возвращают данные, ничего не меняют. Так запросы удобно тестировать
и оптимизировать отдельно от HTTP.
"""
from datetime import timedelta

from django.utils import timezone

from .models import Story


def top_stories(genre_slug: str | None = None, days: int = 7, limit: int = 10) -> list[dict]:
    """Топ рассказов по средней оценке отзывов за последние `days` дней.

    Берём только рассказы хотя бы с одним отзывом в окне. Сортировка: средняя оценка
    по убыванию, затем число отзывов по убыванию.

    TODO(вечер 1): сейчас это ПЛОХАЯ реализация (цикл в Python, запрос на каждый рассказ).
    1. Запустите `make seed`, замерьте время ответа /api/stories/top/.
    2. Перепишите в один запрос: filter + values("story") / annotate(Avg, Count) + order_by + [:limit]
       (или аналог на сыром SQL).
    3. Посмотрите EXPLAIN ANALYZE (QuerySet.explain(analyze=True)) до и после индекса.
       Какой индекс на reviews нужен для фильтра по created_at и группировки по story_id?
    4. Добавьте кэш в Redis (cache-aside, TTL 60 с). Что будет с кэшем при новом отзыве?
    """
    since = timezone.now() - timedelta(days=days)
    stories = Story.objects.filter(status=Story.Status.PUBLISHED)
    if genre_slug:
        stories = stories.filter(genre__slug=genre_slug)

    result = []
    for story in stories:
        ratings = list(story.reviews.filter(created_at__gte=since).values_list("rating", flat=True))
        if not ratings:
            continue
        result.append(
            {
                "story_id": story.pk,
                "title": story.title,
                "avg_rating": round(sum(ratings) / len(ratings), 2),
                "reviews_count": len(ratings),
            }
        )
    result.sort(key=lambda r: (r["avg_rating"], r["reviews_count"]), reverse=True)
    return result[:limit]
