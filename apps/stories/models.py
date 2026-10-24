from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Story(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликован"

    author = models.ForeignKey(
        "authors.AuthorProfile", on_delete=models.CASCADE, related_name="stories"
    )
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT, related_name="stories")
    title = models.CharField(max_length=200)
    text = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    views_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]
        # TODO(вечер 1): после EXPLAIN ANALYZE на seed-данных добавьте индексы здесь.
        # Подсказка: какие поля стоят в WHERE и ORDER BY запросов из selectors.py?
        indexes = []

    def __str__(self):
        return self.title
