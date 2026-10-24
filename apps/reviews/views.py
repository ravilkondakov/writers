from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Review
from .permissions import IsOwnerOrReadOnly
from .serializers import ReviewSerializer


class ReviewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Review.objects.select_related("user")
        story_id = self.request.query_params.get("story")
        if story_id:
            qs = qs.filter(story_id=story_id)
        return qs
