from django.conf import settings
from django.db import models
from django.utils import timezone


class Review(models.Model):
    story = models.ForeignKey("stories.Story", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()
    text = models.TextField(blank=True)
    # default, а не auto_now_add: seed_data должен задавать даты вручную
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(fields=["story", "user"], name="one_review_per_user_story"),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_1_5",
            ),
        ]
        # TODO(вечер 1): какой индекс нужен запросу top_stories? (см. stories/selectors.py)
