import time
from typing import Callable, List, Optional, TYPE_CHECKING

from rosnik.events import queue
from rosnik.types.ai import (
    AIFunctionMetadata,
    AIRequestFinish,
    AIRequestStart,
    ErrorResponseData,
    ResponseData,
)
from rosnik.types.core import Metadata

if TYPE_CHECKING:
    from openai.openai_object import OpenAIObject
    from openai.error import OpenAIError


def track_request_start(
    request_payload: dict, metadata: AIFunctionMetadata, function_fingerprint: List[str]
):
    ai_model = request_payload.get("model")
    user_id = request_payload.get("user")
    ai_provider = metadata.ai_provider
    ai_action = metadata.ai_action
    event = AIRequestStart(
        ai_model=ai_model,
        ai_provider=ai_provider,
        ai_action=ai_action,
        ai_metadata=metadata,
        request_payload=request_payload,
        user_id=user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )
    queue.enqueue_event(event)
    return event


def track_request_finish(
    response_payload: Optional[dict],
    metadata: AIFunctionMetadata,
    function_fingerprint: List[str],
    request_event: AIRequestStart,
    response_serializer: Callable[["OpenAIObject"], ResponseData],
    error_serializer: Callable[["OpenAIError"], ErrorResponseData],
    error: Exception = None,
):
    # Note: this might be different from the request model,
    # e.g. gpt-3.5-turbo in request and gpt-3.5-turbo-0613 in response.
    ai_model = response_payload.get("model") if isinstance(response_payload, dict) else None
    ai_provider = metadata.ai_provider
    ai_action = metadata.ai_action
    response_data = response_serializer(response_payload)
    metadata.openai_attributes.organization = (
        response_data.organization if isinstance(response_data, ResponseData) else None
    )
    metadata.openai_attributes.response_ms = (
        response_data.response_ms if isinstance(response_data, ResponseData) else None
    )
    now = int(time.time_ns() / 1000000)
    event = AIRequestFinish(
        # Manually set this so that response_ms is aligned
        sent_at=now,
        ai_model=ai_model,
        ai_provider=ai_provider,
        ai_action=ai_action,
        ai_metadata=metadata,
        response_payload=response_data.response_payload
        if isinstance(response_data, ResponseData)
        else None,
        response_ms=(now - request_event.sent_at),
        ai_request_start_event_id=request_event.event_id,
        user_id=request_event.user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
        error_data=error_serializer(error),
    )
    queue.enqueue_event(event)
    return event
