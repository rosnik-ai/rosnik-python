from typing import List

from rosnik.events import queue
from rosnik.types.ai import AIFunctionMetadata, AIRequestFinish, AIRequestStart
from rosnik.types.core import Metadata


def track_request_start(
    request_payload: dict, metadata: AIFunctionMetadata, function_fingerprint: List[str]
):
    # TODO: Technically yes, we can pull this from the payload,
    # but this feels precarious.
    ai_model = request_payload["model"]
    ai_provider = metadata["ai_provider"]
    ai_action = metadata["ai_action"]
    # TODO: generate a journey ID
    event = AIRequestStart(
        ai_model=ai_model,
        ai_provider=ai_provider,
        ai_action=ai_action,
        request_payload=request_payload,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )
    queue.enqueue_event(event)
    return event.request_id


# TODO: technically `response_payload` is a openai.openai_object.OpenAIObject
def track_request_finish(
    response_payload: dict,
    metadata: AIFunctionMetadata,
    function_fingerprint: List[str],
    request_id: str,
):
    # TODO: Technically yes, we can pull this from the payload,
    # but this feels precarious.
    ai_model = response_payload["model"]
    ai_provider = metadata["ai_provider"]
    ai_action = metadata["ai_action"]
    # TODO: generate a journey ID
    event = AIRequestFinish(
        ai_model=ai_model,
        ai_provider=ai_provider,
        ai_action=ai_action,
        response_payload=response_payload,
        request_id=request_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )
    queue.enqueue_event(event)
