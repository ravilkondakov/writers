from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from .views import RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", obtain_auth_token),
]
