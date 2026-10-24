from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import AuthorProfile

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    pen_name = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Такой логин уже занят.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"], password=validated_data["password"]
        )
        AuthorProfile.objects.create(
            user=user, pen_name=validated_data.get("pen_name") or user.username
        )
        return user
