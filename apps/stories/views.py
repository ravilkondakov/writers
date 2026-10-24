from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.authors.models import AuthorProfile
from apps.events.producer import publish_story_published, publish_story_viewed

from . import selectors
from .models import Story
from .permissions import IsAuthorOrReadOnly
from .serializers import StorySerializer
from .tasks import notify_story_published


class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        # Все видят опубликованное, автор дополнительно видит свои черновики.
        # TODO(вечер 1): добавьте select_related / annotate, чтобы убрать N+1 (см. serializers.py).
        published = Q(status=Story.Status.PUBLISHED)
        user = self.request.user
        if user.is_authenticated:
            return Story.objects.filter(published | Q(author__user=user))
        return Story.objects.filter(published)

    def perform_create(self, serializer):
        profile, _ = AuthorProfile.objects.get_or_create(
            user=self.request.user, defaults={"pen_name": self.request.user.username}
        )
        serializer.save(author=profile)

    def retrieve(self, request, *args, **kwargs):
        story = self.get_object()
        if story.status == Story.Status.PUBLISHED:
            user_id = request.user.id if request.user.is_authenticated else None
            publish_story_viewed(story.pk, user_id)
        return Response(self.get_serializer(story).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        story = self.get_object()
        if story.status == Story.Status.PUBLISHED:
            return Response({"detail": "Рассказ уже опубликован."}, status=status.HTTP_409_CONFLICT)

        with transaction.atomic():
            story.status = Story.Status.PUBLISHED
            story.published_at = timezone.now()
            story.save(update_fields=["status", "published_at", "updated_at"])
            # on_commit: задача и событие уходят только после успешного коммита,
            # иначе воркер может прочитать рассказ раньше, чем он записан в БД.
            transaction.on_commit(lambda: notify_story_published.delay(story.pk))
            transaction.on_commit(lambda: publish_story_published(story.pk, story.author_id))
        return Response(self.get_serializer(story).data)

    @action(detail=False, methods=["get"])
    def top(self, request):
        genre = request.query_params.get("genre")
        try:
            days = max(1, min(int(request.query_params.get("days", 7)), 90))
            limit = max(1, min(int(request.query_params.get("limit", 10)), 50))
        except ValueError:
            return Response({"detail": "days и limit должны быть числами."}, status=400)
        return Response(selectors.top_stories(genre_slug=genre, days=days, limit=limit))
