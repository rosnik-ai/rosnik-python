from dataclasses import dataclass, field
from typing import TypedDict

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
    # Our own request ID to connect request start + request completion
    request_id: str = field(default_factory=lambda: str(ulid.new()))


@dataclass(kw_only=True, slots=True)
class AIRequestFinish(AIEvent):
    event_type: str = "ai.request.finish"
    # JSONable response payload/body
    response_payload: dict
    request_id: str


@dataclass(kw_only=True, slots=True)
class AIOperationStart(AIEvent):
    pass


@dataclass(kw_only=True, slots=True)
class AIOperationFinish(AIEvent):
    pass
