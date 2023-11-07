"""Patching for v1+ of OpenAI's SDK.

    Currently supports:
    - `openai.OpenAI` and `openai.AzureOpenAI`
    - `chat`
    - `completions`

    Not currently supporting (but let us know if you need it!):
    - `openai.AsyncOpenAI`
    - non-chat models
"""
import functools
import logging
import time
from typing import Callable, Iterator, Union

from rosnik import constants
from rosnik.events import queue
from rosnik.types.core import AIEvent, Metadata
from rosnik.wrap import wrap_class_method
from rosnik.types.ai import (
    AIFunctionMetadata,
    AIRequestFinish,
    AIRequestStartStream,
    AIRequestStart,
    ErrorResponseData,
    OpenAIAttributes,
)

logger = logging.getLogger(__name__)

_OAI = "openai"


def hook_with_metadata(hook: Callable, generate_metadata: Callable[[], AIFunctionMetadata]):
    """Each provider should be encapsulated into what it knows about the call."""
    return functools.partial(hook, generate_metadata=generate_metadata)


def _populate_metadata(metadata: AIFunctionMetadata, instance: object):
    api_type = instance._client.__class__.__name__.lower()
    # Remove the `async` prefix if it exists
    if api_type.startswith("async"):
        api_type = api_type[5:]

    metadata.openai_attributes = OpenAIAttributes(
        # Azure deployment ID is covered under base_url as well.
        api_base=str(instance._client.base_url),
        api_type=api_type,
        api_version=instance._client._custom_query.get("api-version"),
        organization=instance._client.organization,
    )
    return metadata


def request_hook(
    payload: dict,
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
    instance: object = None,
) -> AIRequestStart:
    """`payload` is a dictionary of the `kwargs` provided to `create`.

    Given those kwargs and metadata, generate a AIRequestStart event.
    """
    if not payload:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    metadata = _populate_metadata(generate_metadata(), instance)
    user_id = payload.get("user")

    event = AIRequestStart(
        # OpenAI and Azure both use model now
        ai_model=payload.get("model"),
        ai_provider=metadata.ai_provider,
        ai_action=metadata.ai_action,
        ai_metadata=metadata,
        request_payload=payload,
        user_id=user_id,
        _metadata=Metadata(
            function_fingerprint=function_fingerprint, stream=payload.get("stream", False)
        ),
    )
    queue.enqueue_event(event)
    return event


def response_hook(
    payload: Union[object, Iterator],
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
    instance: object = None,
) -> AIRequestFinish:
    """If we're an Iterator, it means we're a streamed response,
    in which case we're tracking first-byte here.
    If we're an OpenAIObject, then we can provide additional metadata.
    """
    if not payload:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    is_stream_response = isinstance(payload, Iterator)

    metadata = _populate_metadata(generate_metadata(), instance)

    now = int(time.time_ns() / 1000000)
    event_kwargs = {
        # For both OpenAI and Azure, `model` contains the model on the response.
        "ai_model": prior_event.ai_model if is_stream_response else payload.model,
        "ai_provider": metadata.ai_provider,
        "ai_action": metadata.ai_action,
        "ai_metadata": metadata,
        # These are pydantic models, so we need to convert them to dicts.
        "response_payload": None if is_stream_response else payload.model_dump(),
        "sent_at": now,
        "response_ms": (now - prior_event.sent_at),
        "ai_request_start_event_id": prior_event.event_id,
        "user_id": prior_event.user_id,
        "_metadata": Metadata(function_fingerprint=function_fingerprint, stream=is_stream_response),
    }

    if is_stream_response:
        # These don't exist. `payload` is a generator.
        # Make this None
        event_kwargs.pop("response_payload")
        event = AIRequestStartStream(**event_kwargs)
        queue.enqueue_event(event)
        return event

    event = AIRequestFinish(**event_kwargs)
    queue.enqueue_event(event)
    return event


def streamed_response_hook(
    response: Iterator,
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
    instance: object = None,
):
    """Wrap the response generator with our own function so that the
    user can still yield results, and we can automatically
    figure out the duration of the stream.
    """

    content_parts = []
    # Load openai here and use values defined at this point.

    def _stream_hook(line: "BaseModel"):
        """For each chunk, either add it to our content_parts
        or emit an event because we're done.
        """
        if not line:
            logger.debug("Line not seen on stream.")
            return

        if not line.choices or len(line.choices) < 1:
            logger.debug("Missing choices on stream.")
            return

        content = line.choices[0].delta.content
        if content:
            content_parts.append(content)

        finish_reason = line.choices[0].finish_reason
        if finish_reason:
            metadata = _populate_metadata(generate_metadata(), instance)
            now = int(time.time_ns() / 1000000)
            finish_event = AIRequestFinish(
                ai_model=line.model,
                ai_provider=metadata.ai_provider,
                ai_action=metadata.ai_action,
                ai_metadata=metadata,
                # Mimic the OpenAI response payload.
                # Missing `usage`, TODO: what do?
                response_payload={
                    "choices": [
                        {
                            "finish_reason": finish_reason,
                            "index": 0,
                            "message": {"content": "".join(content_parts), "role": "assistant"},
                        }
                    ],
                    "model": line.model,
                    "created": line.created,
                    "object": line.object,
                    "id": line.id,
                },
                sent_at=now,
                response_ms=(now - prior_event.sent_at),
                ai_request_start_event_id=prior_event.event_id,
                user_id=prior_event.user_id,
                _metadata=Metadata(function_fingerprint=function_fingerprint, stream=True),
            )
            queue.enqueue_event(finish_event)

    def _stream_response_wrapper(response: Iterator):
        for line in response:
            _stream_hook(line)
            yield line

    return _stream_response_wrapper(response)


def error_hook(
    error: Exception,
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
    instance: object = None,
) -> AIRequestFinish:
    if error is None:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    metadata = _populate_metadata(generate_metadata(), instance)
    now = int(time.time_ns() / 1000000)
    error_resp = getattr(error, "response", None)
    # Either a dict or a Headers proxy object
    headers = getattr(error_resp, "headers", {})
    body = getattr(error_resp, "content", None)
    event = AIRequestFinish(
        ai_model=None,
        ai_provider=metadata.ai_provider,
        ai_action=metadata.ai_action,
        ai_metadata=metadata,
        error_data=ErrorResponseData(
            message=str(error),
            json_body=None if error_resp is None else error_resp.json(),
            headers=dict(headers),
            organization=instance._client.organization,
            request_id=headers.get("x-request-id"),
            http_status=getattr(error, "status_code", None),
            http_body=None if body is None else body.decode("utf-8"),
            user_message=getattr(error, "message", None),
            code=getattr(error, "code", None),
        ),
        response_ms=(now - prior_event.sent_at),
        ai_request_start_event_id=prior_event.event_id,
        user_id=prior_event.user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )
    queue.enqueue_event(event)
    return event


def _patch_completion(completions_class):
    if getattr(completions_class, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    wrap_class_method(
        completions_class,
        "create",
        hook_with_metadata(
            request_hook,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="completions"),
        ),
        hook_with_metadata(
            response_hook,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="completions"),
        ),
        hook_with_metadata(
            error_hook, lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="completions")
        ),
        hook_with_metadata(
            streamed_response_hook,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="completions"),
        ),
    )

    setattr(completions_class, f"__{constants.NAMESPACE}_patch", True)


def _patch_chat_completion(completions_class):
    if getattr(completions_class, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    wrap_class_method(
        completions_class,
        "create",
        hook_with_metadata(
            request_hook,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions"),
        ),
        hook_with_metadata(
            response_hook,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions"),
        ),
        hook_with_metadata(
            error_hook,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions"),
        ),
        hook_with_metadata(
            streamed_response_hook,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions"),
        ),
    )

    setattr(completions_class, f"__{constants.NAMESPACE}_patch", True)


def patch():
    try:
        from openai import OpenAI
        from openai.resources.chat import completions as chat_completions
        from openai.resources import completions
    except ImportError as e:
        raise e

    if getattr(completions, "Completions", None):
        _patch_completion(completions.Completions)
    if getattr(chat_completions, "Completions", None):
        _patch_chat_completion(chat_completions.Completions)

