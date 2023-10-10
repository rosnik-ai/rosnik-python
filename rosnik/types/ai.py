from dataclasses import dataclass, field
from typing import Optional, TypedDict

from ulid import monotonic as ulid

from rosnik.types.core import AIEvent


class AIFunctionMetadata(TypedDict):
    ai_provider: str
    ai_action: str


@dataclass(kw_only=True, slots=True)
class AIRequestStart(AIEvent):
    event_type: str = "ai.request.start"
    # JSONable request payload
    request_payload: dict


@dataclass(kw_only=True, slots=True)
class AIRequestFinish(AIEvent):
    event_type: str = "ai.request.finish"
    # JSONable response payload/body
    response_payload: dict
    # This is the Event ID of the ai.request.start
    # event that caused this finish action.
    ai_request_start_event_id: str


@dataclass(kw_only=True, slots=True)
class AIOperationStart(AIEvent):
    pass


@dataclass(kw_only=True, slots=True)
class AIOperationFinish(AIEvent):
    pass
