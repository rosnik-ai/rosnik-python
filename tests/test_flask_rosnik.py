import pytest
from flask import Flask, jsonify, request
import ulid

from rosnik import config
from rosnik import flask_rosnik, headers, state
from rosnik.types.ai import AIRequestFinish, AIRequestStart


# Initialize your extension
@pytest.fixture
def app(openai_client):
    app = Flask(__name__)

    @app.get("/")
    def index():
        openai_client.chat.completions.create(
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


@pytest.fixture
def app_with_event_context_hook(openai_client):
    app = Flask(__name__)

    def _request_context():
        host = request.headers.get("host")
        return {"environment": "testing", "host": host}

    @app.get("/")
    def index():
        openai_client.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a world class poet."},
                {"role": "user", "content": "Write a poem about dogs."},
            ],
        )
        return jsonify({"success": True})

    flask_rosnik.FlaskRosnik(app, event_context_hook=_request_context)
    yield app
    state._reset()


# Test case for returned headers
@pytest.mark.vcr
def test_flask_single(app, event_queue):
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
def test_flask_multiple_requests(app, event_queue):
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
        assert event_queue.qsize() == 2
        start_event = event_queue.get()
        assert start_event.journey_id == "test-journey-2"
        assert start_event.device_id == "test-device-2"
        assert start_event.user_interaction_id == "test-user-interaction-2"
        finish_event = event_queue.get()
        assert finish_event.journey_id == "test-journey-2"
        assert finish_event.device_id == "test-device-2"
        assert finish_event.user_interaction_id == "test-user-interaction-2"
        assert event_queue.qsize() == 0


@pytest.mark.vcr
def test_no_headers(app, event_queue):
    """It should generate a new journey ID"""
    with app.test_client() as client:
        res = client.get("/")

        assert headers.JOURNEY_ID_KEY in res.headers
        assert isinstance(ulid.parse(res.headers.get(headers.JOURNEY_ID_KEY)), ulid.ULID)
        assert state.retrieve(state.State.USER_INTERACTION_ID) is None
        assert state.retrieve(state.State.DEVICE_ID) is None

        assert res.json == {"success": True}

        assert event_queue.qsize() == 2
        event_queue.get()
        event_queue.get()
        assert event_queue.qsize() == 0


def test_client_init(mocker, app):
    patch_init = mocker.patch("rosnik.client.init")  # Mock the client initialization
    flask_rosnik.FlaskRosnik(app)
    patch_init.assert_called_once()


def test_client_init__with_params():
    def _custom_hook():
        return {}

    test_app = Flask(__name__)
    ext = flask_rosnik.FlaskRosnik(
        test_app,
        api_key="test_key",
        sync_mode=True,
        environment="development",
        event_context_hook=_custom_hook,
    )
    ext.init_app(test_app)
    assert config.Config.api_key == "test_key"
    assert config.Config.sync_mode is True
    assert config.Config.environment == "development"
    assert config.Config.event_context_hook is _custom_hook


@pytest.mark.vcr
def test_flask_with_context(app_with_event_context_hook, event_queue):
    with app_with_event_context_hook.test_client() as client:
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
        assert event_queue.qsize() == 2

        start_event: AIRequestStart = event_queue.get()
        assert start_event.journey_id == "test-journey"
        assert start_event.device_id == "test-device"
        assert start_event.user_interaction_id == "test-user-interaction"
        assert start_event._metadata.environment == "testing"
        assert start_event.context == {"host": "localhost"}

        finish_event: AIRequestFinish = event_queue.get()
        assert finish_event.journey_id == "test-journey"
        assert finish_event.device_id == "test-device"
        assert finish_event.user_interaction_id == "test-user-interaction"
        assert finish_event._metadata.environment == "testing"
        assert finish_event.context == {"host": "localhost"}

        assert event_queue.qsize() == 0
