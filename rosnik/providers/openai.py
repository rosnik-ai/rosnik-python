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

try:
    from openai.openai_object import OpenAIObject
except ImportError as e:
    raise e

logger = logging.getLogger(__name__)

_OAI = "openai"


def hook_with_metadata(hook: Callable, generate_metadata: Callable[[], AIFunctionMetadata]):
    """Each provider should be encapsulated into what it knows about the call."""
    return functools.partial(hook, generate_metadata=generate_metadata)


def request_hook(
    payload: dict,
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
) -> AIRequestStart:
    """`payload` is a dictionary of the `kwargs` provided to `create`.

    Given those kwargs and metadata, generate a AIRequestStart event.
    """
    if not payload:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    # Reimport to make sure we have the latest values
    import openai

    metadata = generate_metadata()
    metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base,
        api_type=openai.api_type,
        api_version=openai.api_version,
        organization=openai.organization,
    )

    ai_model = (
        payload.get("model")
        if openai.api_type == "open_ai"
        else (payload.get("deployment_id") or payload.get("engine"))
    )
    user_id = payload.get("user")

    event = AIRequestStart(
        ai_model=ai_model,
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
    payload: Union["OpenAIObject", Iterator],
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
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

    # Reimport to make sure we have the latest values
    import openai

    is_stream_response = isinstance(payload, Iterator)

    metadata = generate_metadata()
    metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base,
        api_type=openai.api_type,
        api_version=openai.api_version,
        organization=openai.organization,
    )

    now = int(time.time_ns() / 1000000)
    event_kwargs = {
        # For both OpenAI and Azure, `model` contains the model on the response.
        "ai_model": prior_event.ai_model if is_stream_response else payload.get("model"),
        "ai_provider": metadata.ai_provider,
        "ai_action": metadata.ai_action,
        "ai_metadata": metadata,
        "response_payload": payload,
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
):
    """Wrap the response generator with our own function so that the
    user can still yield results, and we can automatically
    figure out the duration of the stream.
    """

    content_parts = []
    # Load openai here and use values defined at this point.
    import openai

    def _stream_hook(line: "OpenAIObject"):
        """For each chunk, either add it to our content_parts
        or emit an event because we're done.
        """
        if not line:
            logger.debug("Line not seen on stream.")
            return

        choices = line.get("choices")
        if not choices or len(choices) < 1:
            logger.debug("Missing choices on stream.")
            return

        content = choices[0].get("delta", {}).get("content")
        if content:
            content_parts.append(content)

        finish_reason = choices[0].get("finish_reason")
        if finish_reason:
            metadata = generate_metadata()
            metadata.openai_attributes = OpenAIAttributes(
                api_base=openai.api_base,
                api_type=openai.api_type,
                api_version=openai.api_version,
                organization=openai.organization,
            )
            now = int(time.time_ns() / 1000000)
            finish_event = AIRequestFinish(
                ai_model=line.get("model"),
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
                    "model": line.get("model"),
                    "created": line.get("created"),
                    "object": line.get("object"),
                    "id": line.get("id"),
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
) -> AIRequestFinish:
    if error is None:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    import openai

    metadata = generate_metadata()
    metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base,
        api_type=openai.api_type,
        api_version=openai.api_version,
        organization=openai.organization,
    )

    now = int(time.time_ns() / 1000000)
    event = AIRequestFinish(
        ai_model=None,
        ai_provider=metadata.ai_provider,
        ai_action=metadata.ai_action,
        ai_metadata=metadata,
        error_data=ErrorResponseData(
            message=str(error),
            json_body=getattr(error, "json_body", None),
            headers=getattr(error, "headers", None),
            organization=getattr(error, "organization", None),
            request_id=getattr(error, "request_id", None),
            http_status=getattr(error, "http_status", None),
            http_body=getattr(error, "http_body", None),
            user_message=getattr(error, "user_message", None),
            code=getattr(error, "code", None),
        ),
        response_ms=(now - prior_event.sent_at),
        ai_request_start_event_id=prior_event.event_id,
        user_id=prior_event.user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )
    queue.enqueue_event(event)
    return event


def _patch_completion(openai):
    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    wrap_class_method(
        openai.Completion,
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


def _patch_chat_completion(openai):
    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    wrap_class_method(
        openai.ChatCompletion,
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


def _patch_openai():
    try:
        import openai
    except ImportError as e:
        raise e

    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    if getattr(openai, "Completion", None):
        _patch_completion(openai)
    if getattr(openai, "ChatCompletion", None):
        _patch_chat_completion(openai)
    setattr(openai, f"__{constants.NAMESPACE}_patch", True)
