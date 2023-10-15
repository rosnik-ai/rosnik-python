import pytest
from flask import Flask, jsonify
import ulid

from rosnik import flask_rosnik, headers, state
from rosnik.events import queue


# Initialize your extension
@pytest.fixture
def app(mocker):
    mocker.patch("rosnik.events.queue.EventProcessor")
    app = Flask(__name__)

    @app.get("/")
    def index():
        import openai

        openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a world class poet."},
                {"role": "user", "content": "Write a poem about dogs."},
            ],
        )
        return jsonify({"success": True})

    flask_rosnik.FlaskRosnik(app)
    yield app
    state._reset()


# Test case for returned headers
@pytest.mark.vcr
def test_flask_single(app):
    with app.test_client() as client:
        res = client.get(
            "/",
            headers={
                headers.JOURNEY_ID_KEY: "test-journey",
                headers.DEVICE_ID_KEY: "test-device",
                headers.INTERACTION_ID_KEY: "test-user-interaction",
            },
        )
        assert headers.JOURNEY_ID_KEY in res.headers
        assert res.headers.get(headers.JOURNEY_ID_KEY) == "test-journey"
        assert queue.event_queue.qsize() == 2
        start_event = queue.event_queue.get()
        assert start_event.journey_id == "test-journey"
        assert start_event.device_id == "test-device"
        assert start_event.user_interaction_id == "test-user-interaction"
        finish_event = queue.event_queue.get()
        assert finish_event.journey_id == "test-journey"
        assert finish_event.device_id == "test-device"
        assert finish_event.user_interaction_id == "test-user-interaction"
        assert queue.event_queue.qsize() == 0


@pytest.mark.vcr
def test_flask_multiple_requests(app):
    with app.test_client() as client:
        res = client.get(
            "/",
            headers={
                headers.JOURNEY_ID_KEY: "test-journey",
                headers.DEVICE_ID_KEY: "test-device",
                headers.INTERACTION_ID_KEY: "test-user-interaction",
            },
        )
        assert headers.JOURNEY_ID_KEY in res.headers
        assert res.headers.get(headers.JOURNEY_ID_KEY) == "test-journey"
        assert queue.event_queue.qsize() == 2
        start_event = queue.event_queue.get()
        assert start_event.journey_id == "test-journey"
        assert start_event.device_id == "test-device"
        assert start_event.user_interaction_id == "test-user-interaction"
        finish_event = queue.event_queue.get()
        assert finish_event.journey_id == "test-journey"
        assert finish_event.device_id == "test-device"
        assert finish_event.user_interaction_id == "test-user-interaction"
        assert queue.event_queue.qsize() == 0

        res = client.get(
            "/",
            headers={
                headers.JOURNEY_ID_KEY: "test-journey-2",
                headers.DEVICE_ID_KEY: "test-device-2",
                headers.INTERACTION_ID_KEY: "test-user-interaction-2",
            },
        )
        assert headers.JOURNEY_ID_KEY in res.headers
        assert res.headers.get(headers.JOURNEY_ID_KEY) == "test-journey-2"
        assert queue.event_queue.qsize() == 2
        start_event = queue.event_queue.get()
        assert start_event.journey_id == "test-journey-2"
        assert start_event.device_id == "test-device-2"
        assert start_event.user_interaction_id == "test-user-interaction-2"
        finish_event = queue.event_queue.get()
        assert finish_event.journey_id == "test-journey-2"
        assert finish_event.device_id == "test-device-2"
        assert finish_event.user_interaction_id == "test-user-interaction-2"
        assert queue.event_queue.qsize() == 0

@pytest.mark.vcr
def test_no_headers(app):
    """It should generate a new journey ID"""
    with app.test_client() as client:
        res = client.get("/")

        assert headers.JOURNEY_ID_KEY in res.headers 
        assert isinstance(ulid.parse(res.headers.get(headers.JOURNEY_ID_KEY)), ulid.ULID)
        assert state.retrieve(state.State.USER_INTERACTION_ID) is None  
        assert state.retrieve(state.State.DEVICE_ID) is None

        assert res.json == {"success": True}
        
        assert queue.event_queue.qsize() == 2


@pytest.mark.vcr
def test_client_init(mocker, app):
    patch_init = mocker.patch("rosnik.client.init")  # Mock the client initialization
    flask_rosnik.FlaskRosnik(app)
    patch_init.assert_called_once()