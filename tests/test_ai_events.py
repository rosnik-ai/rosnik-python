import os
import time
import platform
import pytest

import rosnik
from rosnik import config
from rosnik.providers import openai_v1 as openai_
from rosnik.types.ai import AIRequestFinish, AIRequestStart, AIRequestStartStream

import ulid

from rosnik.types.core import Event


def validate_common_attributes(event: Event):
    assert isinstance(ulid.parse(event.event_id), ulid.ULID)
    assert isinstance(ulid.parse(event.journey_id), ulid.ULID)
    assert event.sent_at == (int(time.time_ns() / 1000000))
    assert event.device_id is None
    assert event._metadata
    assert event._metadata.environment is None
    assert event._metadata.runtime == platform.python_implementation()
    assert event._metadata.runtime_version == platform.python_version()
    assert event._metadata.sdk_version == "0.0.37"
    assert event._metadata.function_fingerprint
    assert len(event._metadata.function_fingerprint.split(".")) == 10
    assert event.context is None


@pytest.mark.vcr
def test_chat_completion(openai_client, openai_chat_completions_class, event_queue, freezer):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    openai_._patch_chat_completion(openai_chat_completions_class)
    assert event_queue.qsize() == 0
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]
    openai_client.chat.completions.create(
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
    assert start_event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert start_event.ai_metadata.openai_attributes.api_type == "openai"
    assert start_event.ai_metadata.openai_attributes.api_version is None
    assert start_event.ai_request_start_event_id == start_event.event_id

    assert isinstance(finish_event, AIRequestFinish)
    validate_common_attributes(finish_event)
    assert finish_event.event_type == "ai.request.finish"
    assert finish_event.ai_model == "gpt-3.5-turbo-0613"
    assert finish_event.ai_request_start_event_id == start_event.event_id
    assert finish_event.ai_metadata
    assert finish_event.ai_metadata.ai_provider == "openai"
    assert finish_event.ai_metadata.ai_action == "chat.completions"
    assert finish_event.ai_metadata.openai_attributes is not None
    assert start_event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert start_event.ai_metadata.openai_attributes.api_type == "openai"
    assert start_event.ai_metadata.openai_attributes.api_version is None
    assert finish_event.response_ms == (finish_event.sent_at - start_event.sent_at)


@pytest.mark.vcr
def test_event_with_context(openai_client, event_queue):
    def _custom_hook():
        return {"environment": "testing", "test-key": "test-value", "test-key2": "test-value2"}

    rosnik.init(event_context_hook=_custom_hook)
    # The default environment is not set
    assert config.Config.environment is None
    assert config.Config.event_context_hook is _custom_hook

    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]
    openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=expected_messages,
    )

    start_event: AIRequestStart = event_queue.get()
    assert start_event._metadata.environment == "testing"
    assert start_event.context == {"test-key": "test-value", "test-key2": "test-value2"}

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event._metadata.environment == "testing"
    assert finish_event.context == {"test-key": "test-value", "test-key2": "test-value2"}


@pytest.mark.skipif(os.environ.get("CI") == "true", reason="CI doesn't support streaming")
def test_event_with_context__streaming(openai_client, event_queue):
    def _custom_hook():
        return {"environment": "testing", "test-key": "test-value", "test-key2": "test-value2"}

    rosnik.init(event_context_hook=_custom_hook)
    # The default environment is not set
    assert config.Config.environment is None
    assert config.Config.event_context_hook is _custom_hook

    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]
    resp = openai_client.chat.completions.create(
        model="gpt-3.5-turbo", messages=expected_messages, stream=True
    )

    # Stream
    [_ for _ in resp]

    assert event_queue.qsize() == 3
    start_event: AIRequestStart = event_queue.get()
    assert start_event._metadata.environment == "testing"
    assert start_event.context == {"test-key": "test-value", "test-key2": "test-value2"}

    start_stream: AIRequestStartStream = event_queue.get()
    assert start_stream._metadata.environment == "testing"
    assert start_stream.context == {"test-key": "test-value", "test-key2": "test-value2"}

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event._metadata.environment == "testing"
    assert finish_event.context == {"test-key": "test-value", "test-key2": "test-value2"}


@pytest.mark.vcr
def test_event_with_error_doesnt_raise(openai_client, event_queue, caplog):
    """Check that we don't raise exceptions if a user defined function
    fails. And if there's a default environment, we should use it.
    """

    def _custom_hook():
        raise Exception("oh no")

    rosnik.init(event_context_hook=_custom_hook, environment="pytest")
    assert config.Config.environment == "pytest"
    assert config.Config.event_context_hook is _custom_hook

    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]
    openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=expected_messages,
    )

    start_event: AIRequestStart = event_queue.get()
    # pytest because context didn't set anything
    assert start_event._metadata.environment == "pytest"
    # None because context hook exploded
    assert start_event.context is None

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event._metadata.environment == "pytest"
    # None because context hook exploded
    assert finish_event.context is None

    assert len(caplog.records) == 2
    for record in caplog.records:
        assert str(record.exc_info[1]) == "oh no"
        assert "Could not generate context from _custom_hook" == record.message


@pytest.mark.vcr
def test_event_with_context_manager(openai_client, event_queue):
    def _custom_hook():
        return {"environment": "testing", "test-key": "test-value", "test-key2": "test-value2"}

    rosnik.init(event_context_hook=_custom_hook)
    # The default environment is not set
    assert config.Config.environment is None
    assert config.Config.event_context_hook is _custom_hook

    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]
    # This has prompt metadata
    with rosnik.context(prompt_name="test-label"):
        openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=expected_messages,
        )
        openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=expected_messages,
        )
    # This doesn't
    openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=expected_messages,
    )

    assert event_queue.qsize() == 6

    start_event: AIRequestStart = event_queue.get()
    assert start_event._metadata.environment == "testing"
    assert start_event.context == {
        "test-key": "test-value",
        "test-key2": "test-value2",
        "prompt_name": "test-label",
    }

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event._metadata.environment == "testing"
    assert finish_event.context == {
        "test-key": "test-value",
        "test-key2": "test-value2",
        "prompt_name": "test-label",
    }

    start_event: AIRequestStart = event_queue.get()
    assert start_event._metadata.environment == "testing"
    assert start_event.context == {
        "test-key": "test-value",
        "test-key2": "test-value2",
        "prompt_name": "test-label",
    }

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event._metadata.environment == "testing"
    assert finish_event.context == {
        "test-key": "test-value",
        "test-key2": "test-value2",
        "prompt_name": "test-label",
    }

    start_event: AIRequestStart = event_queue.get()
    assert start_event._metadata.environment == "testing"
    assert start_event.context == {"test-key": "test-value", "test-key2": "test-value2"}

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event._metadata.environment == "testing"
    assert finish_event.context == {"test-key": "test-value", "test-key2": "test-value2"}


@pytest.mark.vcr
def test_event_with_context_manager__stacked(openai_client, event_queue):
    rosnik.init()

    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]

    # This has event-level context
    with rosnik.context(prompt_name="test-label"):
        openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=expected_messages,
        )

        with rosnik.context(prompt_name="test-label2"):
            openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=expected_messages,
            )

        # This should have "test-label" context
        openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=expected_messages,
        )

    # This should have no context
    openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=expected_messages,
    )

    assert event_queue.qsize() == 8

    start_event: AIRequestStart = event_queue.get()
    assert start_event.context == {"prompt_name": "test-label"}

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event.context == {"prompt_name": "test-label"}

    start_event: AIRequestStart = event_queue.get()
    assert start_event.context == {"prompt_name": "test-label2"}

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event.context == {"prompt_name": "test-label2"}

    start_event: AIRequestStart = event_queue.get()
    assert start_event.context == {"prompt_name": "test-label"}

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event.context == {"prompt_name": "test-label"}

    start_event: AIRequestStart = event_queue.get()
    assert start_event.context is None

    finish_event: AIRequestFinish = event_queue.get()
    assert finish_event.context is None
