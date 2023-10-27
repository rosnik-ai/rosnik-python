import pytest

import openai
import django
from django.http import HttpResponse
from django.test import RequestFactory
from django.conf import settings

from rosnik import headers
from rosnik.frameworks.django import rosnik_middleware

settings.configure(
    ROSNIK_API_KEY="your_test_api_key",
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
)
django.setup()


# Mock a view for testing
def mock_view(request):
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a world class poet."},
            {"role": "user", "content": "Write a poem about dogs."},
        ],
    )
    return HttpResponse({"success": True})


# Mock middleware wrapped view
mock_view = rosnik_middleware(mock_view)


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.vcr
def test_middleware_headers(request_factory, event_queue):
    request = request_factory.get(
        "/",
        **{
            headers.JOURNEY_ID_KEY: "test-journey",
            headers.DEVICE_ID_KEY: "test-device",
            headers.INTERACTION_ID_KEY: "test-user-interaction",
        }
    )
    response = mock_view(request)
    assert headers.JOURNEY_ID_KEY in response.headers
    assert response.headers[headers.JOURNEY_ID_KEY] == "test-journey"
    assert event_queue.qsize() == 2
    start_event = event_queue.get()
    assert start_event.journey_id == "test-journey"
    assert start_event.device_id == "test-device"
    assert start_event.user_interaction_id == "test-user-interaction"
    finish_event = event_queue.get()
    assert finish_event.journey_id == "test-journey"
    assert finish_event.device_id == "test-device"
    assert finish_event.user_interaction_id == "test-user-interaction"
    assert event_queue.qsize() == 0


@pytest.mark.vcr
def test_no_headers(request_factory, event_queue):
    """We should generate new journey IDs for each request."""
    request = request_factory.get("/")
    response = mock_view(request)

    assert headers.JOURNEY_ID_KEY in response.headers
    assert event_queue.qsize() == 2
    journey_id = response.headers.get(headers.JOURNEY_ID_KEY)
    start_event = event_queue.get()
    assert start_event.journey_id == journey_id
    finish_event = event_queue.get()
    assert finish_event.journey_id == journey_id

    response = mock_view(request)
    assert headers.JOURNEY_ID_KEY in response.headers
    assert event_queue.qsize() == 2
    journey_id_2 = response.headers.get(headers.JOURNEY_ID_KEY)
    assert journey_id_2 != journey_id
    start_event_2 = event_queue.get()
    assert start_event_2.journey_id == journey_id_2
    assert start_event_2.journey_id != start_event.journey_id
    finish_event_2 = event_queue.get()
    assert finish_event_2.journey_id == journey_id_2
    assert finish_event_2.journey_id != finish_event.journey_id
