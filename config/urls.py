from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.authors.urls")),
    path("api/", include("apps.stories.urls")),
    path("api/", include("apps.reviews.urls")),
]
