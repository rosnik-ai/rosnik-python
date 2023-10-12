import pytest
from flask import Flask, jsonify

from rosnik import flask_rosnik, headers
from rosnik.events import queue


# Initialize your extension
@pytest.fixture
def app(mocker):
    mocker.patch("threading.Thread")
    app = Flask(__name__)

    @app.get("/")
    def index():
        import openai

        openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are dog"},
                {"role": "user", "content": "Bark"},
            ],
        )
        return jsonify({"success": True})

    flask_rosnik.FlaskRosnik(app)
    return app


# Test case for returned headers
def test_flask(app):
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
        # Similarly add assertions for all the expected headers
