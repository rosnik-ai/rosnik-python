import platform
import time

import pytest

from rosnik import collector
from rosnik.types.core import Metadata


@pytest.fixture
def added_fake_event():
    payload = {
        "model": "text-davinci-003",
        "prompt": "Suggest three names for an animal that is a superhero.\n\nAnimal: Cat\nNames: Captain Sharpclaw, Agent Fluffball, The Incredible Feline\nAnimal: Dog\nNames: Ruff the Protector, Wonder Canine, Sir Barks-a-Lot\nAnimal: Mixed mini poodle\nNames:",
        "temperature": 0.6,
    }
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "logprobs": "null",
                "text": " Wonder Woof, Major Fluff, Super Poodle",
            }
        ],
        "created": 1684268025,
        "id": "cmpl-7GvLFZdFXxzQjYWruCGTHowvfU1xO",
        "model": "text-davinci-003",
        "object": "text_completion",
        "usage": {"completion_tokens": 11, "prompt_tokens": 65, "total_tokens": 76},
    }
    function_fingerprint = [
        "get_stack_frames",
        "wrapper",
        "index",
        "dispatch_request",
        "full_dispatch_request",
        "wsgi_app",
    ]
    start_time = time.time()
    end_time = time.time() + 100
    completion_metadata: Metadata = {"platform": "openai", "action": "completion"}
    collector.capture_data(
        payload, response, function_fingerprint, start_time, end_time, completion_metadata
    )
    return (payload, response, function_fingerprint, start_time, end_time, completion_metadata)


def test_capture_data(event_queue, added_fake_event):
    (
        payload,
        response,
        function_fingerprint,
        start_time,
        end_time,
        completion_metadata,
    ) = added_fake_event
    assert event_queue.qsize() == 1
    event = event_queue.get()
    assert event["request"] == payload
    assert event["response"] == response
    assert event["function_fingerprint"] == function_fingerprint
    assert event["start_time"] == start_time
    assert event["end_time"] == end_time
    assert event["_prompthq_metadata"] == completion_metadata


def test_enqueue_feedback(mocker, event_queue, added_fake_event):
    mocker.patch("time.time", return_value=123456789)
    (
        _,
        response,
        _,
        _,
        _,
        _,
    ) = added_fake_event
    assert event_queue.qsize() == 1
    _ = event_queue.get()
    assert event_queue.qsize() == 0
    collector.enqueue_feedback(
        completion_id=response["id"],
        user_id=None,
        score=10,
        metadata={"comment": "Great completion!"},
    )
    assert event_queue.qsize() == 1
    event = event_queue.get()
    expected_dict = {
        "timestamp": 123456789,
        "completion_id": response["id"],
        "user_id": None,
        "score": 10,
        "metadata": {"comment": "Great completion!"},
        "_prompthq_metadata": {
            "platform": "openai",
            "action": "feedback",
            "lang": platform.python_version(),
            "environment": "production",
        },
    }
    assert event == expected_dict
