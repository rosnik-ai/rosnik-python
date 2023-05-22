import time

import pytest

from promptly import collector
from promptly.types import PromptHqMetadata


@pytest.fixture
def event_queue():
    yield collector.event_queue
    # Clear queue
    while collector.event_queue.qsize() > 0:
        collector.event_queue.get(block=False)


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
    completion_metadata: PromptHqMetadata = {"platform": "openai", "action": "completion"}
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
