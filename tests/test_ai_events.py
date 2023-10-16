import platform
import pytest

from rosnik.providers import openai as openai_
from rosnik.types.ai import AIRequestFinish, AIRequestStart

import ulid

from rosnik.types.core import Event


def validate_common_attributes(event: Event):
    assert isinstance(ulid.parse(event.event_id), ulid.ULID)
    assert isinstance(ulid.parse(event.journey_id), ulid.ULID)
    assert event.sent_at
    assert event.device_id is None
    assert event._metadata
    assert event._metadata.environment is None
    assert event._metadata.runtime == platform.python_implementation()
    assert event._metadata.runtime_version == platform.python_version()
    assert event._metadata.sdk_version == "0.0.23"
    assert event._metadata.function_fingerprint
    assert len(event._metadata.function_fingerprint.split(".")) == 5


@pytest.mark.vcr
def test_chat_completion(openai, event_queue):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    openai_._patch_chat_completion(openai)
    assert event_queue.qsize() == 0
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=expected_messages,
    )
    assert event_queue.qsize() == 2
    start_event = event_queue.get()
    finish_event = event_queue.get()

    assert isinstance(start_event, AIRequestStart)
    validate_common_attributes(start_event)
    assert start_event.event_type == "ai.request.start"
    assert start_event.ai_model == "gpt-3.5-turbo"
    assert start_event.ai_provider == "openai"
    assert start_event.ai_action == "chat.completions"
    assert start_event.request_payload["messages"] == expected_messages
    assert start_event.ai_metadata
    assert start_event.ai_metadata.ai_provider == "openai"
    assert start_event.ai_metadata.ai_action == "chat.completions"
    assert start_event.ai_metadata.openai_attributes is not None
    assert start_event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert start_event.ai_metadata.openai_attributes.api_type == "open_ai"
    assert start_event.ai_metadata.openai_attributes.api_version is None

    assert isinstance(finish_event, AIRequestFinish)
    validate_common_attributes(finish_event)
    assert finish_event.event_type == "ai.request.finish"
    assert finish_event.ai_model == "gpt-3.5-turbo-0613"
    assert finish_event.ai_request_start_event_id == start_event.event_id
    assert finish_event.ai_metadata
    assert finish_event.ai_metadata.ai_provider == "openai"
    assert finish_event.ai_metadata.ai_action == "chat.completions"
    assert finish_event.ai_metadata.openai_attributes is not None
    assert start_event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert start_event.ai_metadata.openai_attributes.api_type == "open_ai"
    assert start_event.ai_metadata.openai_attributes.api_version is None
    assert finish_event.response_ms == (finish_event.sent_at - start_event.sent_at)
