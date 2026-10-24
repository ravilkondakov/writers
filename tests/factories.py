import factory
from django.contrib.auth import get_user_model

from apps.authors.models import AuthorProfile
from apps.reviews.models import Review
from apps.stories.models import Genre, Story


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}")
    password = "!"


class AuthorProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuthorProfile

    user = factory.SubFactory(UserFactory)
    pen_name = factory.Sequence(lambda n: f"Автор {n}")


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Sequence(lambda n: f"Жанр {n}")
    slug = factory.Sequence(lambda n: f"genre-{n}")


class StoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Story

    author = factory.SubFactory(AuthorProfileFactory)
    genre = factory.SubFactory(GenreFactory)
    title = factory.Sequence(lambda n: f"Рассказ {n}")
    text = "Текст"
    status = Story.Status.PUBLISHED


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    story = factory.SubFactory(StoryFactory)
    user = factory.SubFactory(UserFactory)
    rating = 5
