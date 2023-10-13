from typing import Callable, List

from rosnik.events import queue
from rosnik.types.ai import AIFunctionMetadata, AIRequestFinish, AIRequestStart
from rosnik.types.core import Metadata


def track_request_start(
    request_payload: dict, metadata: AIFunctionMetadata, function_fingerprint: List[str]
):
    # TODO: Technically yes, we can pull this from the payload,
    # but this feels precarious.
    ai_model = request_payload["model"]
    # TODO: we should have a serializer:
    # OpenAI calls this "user"
    user_id = request_payload.get("user", None)
    ai_provider = metadata["ai_provider"]
    ai_action = metadata["ai_action"]
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
    response_payload,
    metadata: AIFunctionMetadata,
    function_fingerprint: List[str],
    request_event: AIRequestStart,
    response_serializer: Callable
):
    # Note: this might be different from the request model,
    # e.g. gpt-3.5-turbo in request and gpt-3.5-turbo-0613 in response.
    ai_model = response_payload["model"]
    ai_provider = metadata["ai_provider"]
    ai_action = metadata["ai_action"]
    event = AIRequestFinish(
        ai_model=ai_model,
        ai_provider=ai_provider,
        ai_action=ai_action,
        ai_metadata=metadata,
        response_payload=response_serializer(response_payload),
        ai_request_start_event_id=request_event.event_id,
        user_id=request_event.user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )
    queue.enqueue_event(event)
    return event
