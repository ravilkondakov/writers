from rest_framework import serializers

from apps.stories.models import Story

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "story", "user", "username", "rating", "text", "created_at"]
        read_only_fields = ["created_at"]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Оценка от 1 до 5.")
        return value

    def validate_story(self, story):
        if story.status != Story.Status.PUBLISHED:
            raise serializers.ValidationError("Отзыв можно оставить только на опубликованный рассказ.")
        if story.author.user_id == self.context["request"].user.id:
            raise serializers.ValidationError("Нельзя оценивать собственный рассказ.")
        return story

    def validate(self, attrs):
        user = self.context["request"].user
        if Review.objects.filter(story=attrs["story"], user=user).exists():
            raise serializers.ValidationError("Вы уже оставляли отзыв на этот рассказ.")
        return attrs
