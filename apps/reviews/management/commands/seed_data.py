"""Генерирует данные для упражнений с производительностью.

Пример: python manage.py seed_data --stories 5000 --reviews 1000000
На PostgreSQL 1 млн отзывов создаётся за пару минут (bulk_create пачками).
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.authors.models import AuthorProfile
from apps.reviews.models import Review
from apps.stories.models import Genre, Story

GENRES = ["Хоррор", "Детектив", "Антиутопия", "Триллер", "Мистика", "Фантастика"]
BATCH = 10_000


class Command(BaseCommand):
    help = "Создаёт тестовые жанры, пользователей, рассказы и отзывы."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=1000)
        parser.add_argument("--authors", type=int, default=200)
        parser.add_argument("--stories", type=int, default=5000)
        parser.add_argument("--reviews", type=int, default=100_000)

    def handle(self, *args, **opts):
        users_n, authors_n = opts["users"], opts["authors"]
        stories_n, reviews_n = opts["stories"], opts["reviews"]
        if authors_n > users_n:
            raise CommandError("--authors не может быть больше --users")
        if reviews_n > stories_n * users_n:
            raise CommandError("Слишком много отзывов: пары (рассказ, пользователь) уникальны.")

        User = get_user_model()
        now = timezone.now()
        rng = random.Random(42)  # фиксированное зерно: данные повторяемы

        genres = [
            Genre.objects.get_or_create(name=name, defaults={"slug": f"genre-{i}"})[0]
            for i, name in enumerate(GENRES)
        ]
        start = User.objects.count()
        User.objects.bulk_create(
            [User(username=f"seed{start + i}", password="!") for i in range(users_n)],
            batch_size=BATCH,
        )
        users = list(User.objects.filter(username__startswith="seed").order_by("id")[:users_n])
        AuthorProfile.objects.bulk_create(
            [AuthorProfile(user=u, pen_name=f"Автор {u.pk}") for u in users[:authors_n]],
            batch_size=BATCH,
            ignore_conflicts=True,
        )
        authors = list(AuthorProfile.objects.filter(user__in=users[:authors_n]))

        stories = []
        for i in range(stories_n):
            published = rng.random() < 0.9
            stories.append(
                Story(
                    author=rng.choice(authors),
                    genre=rng.choice(genres),
                    title=f"Рассказ {i}",
                    text="Текст рассказа. " * 20,
                    status=Story.Status.PUBLISHED if published else Story.Status.DRAFT,
                    published_at=now - timedelta(days=rng.randint(0, 60)) if published else None,
                )
            )
        Story.objects.bulk_create(stories, batch_size=BATCH)
        story_ids = list(Story.objects.filter(status=Story.Status.PUBLISHED).values_list("pk", flat=True))
        self.stdout.write(f"Рассказов: {len(story_ids)} опубликовано")

        # уникальные пары (рассказ, пользователь) без повторов
        user_ids = [u.pk for u in users]
        total_pairs = len(story_ids) * len(user_ids)
        count = min(reviews_n, total_pairs)
        buffer = []
        for pair in rng.sample(range(total_pairs), count):
            s_idx, u_idx = divmod(pair, len(user_ids))
            buffer.append(
                Review(
                    story_id=story_ids[s_idx],
                    user_id=user_ids[u_idx],
                    rating=rng.randint(1, 5),
                    created_at=now - timedelta(days=rng.randint(0, 30), minutes=rng.randint(0, 1439)),
                )
            )
            if len(buffer) >= BATCH:
                Review.objects.bulk_create(buffer)
                buffer = []
        if buffer:
            Review.objects.bulk_create(buffer)
        self.stdout.write(self.style.SUCCESS(f"Готово: {count} отзывов"))
