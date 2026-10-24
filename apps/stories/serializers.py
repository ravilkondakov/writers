from django.db.models import Avg
from rest_framework import serializers

from .models import Story


class StorySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.pen_name", read_only=True)
    genre_name = serializers.CharField(source="genre.name", read_only=True)
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            "id",
            "title",
            "text",
            "genre",
            "genre_name",
            "author_name",
            "status",
            "published_at",
            "views_count",
            "avg_rating",
            "created_at",
        ]
        read_only_fields = ["status", "published_at", "views_count", "created_at"]

    def get_avg_rating(self, obj):
        # TODO(вечер 1): ЗДЕСЬ ПРОБЛЕМА N+1. Отдельный запрос на каждый рассказ в списке,
        # плюс ещё запросы на author и genre. Задача: список из 20 рассказов
        # должен делаться за ≤ 4 запроса. Используйте select_related и annotate(Avg) во
        # views.get_queryset и читайте готовое значение здесь. Затем уберите xfail в
        # tests/test_query_counts.py.
        return obj.reviews.aggregate(avg=Avg("rating"))["avg"]
