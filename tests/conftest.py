import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_cache():
    """Кэш (и счётчики throttling) не должны протекать между тестами."""
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()
