from dataclasses import dataclass
from typing import Optional, TypedDict


from rosnik.types.core import AIEvent


class OpenAIAttributes(TypedDict):
    api_base: str
    api_type: str
    api_version: str


@dataclass(kw_only=True, slots=True)
class AIFunctionMetadata:
    ai_provider: str
    ai_action: str
    openai_attributes: Optional[OpenAIAttributes] = None


@dataclass(kw_only=True, slots=True)
class AIRequestStart(AIEvent):
    event_type: str = "ai.request.start"
    # JSONable request payload
    request_payload: dict
    ai_metadata: AIFunctionMetadata


@dataclass(kw_only=True, slots=True)
class AIRequestFinish(AIEvent):
    event_type: str = "ai.request.finish"
    # JSONable response payload/body
    response_payload: dict
    # This is the Event ID of the ai.request.start
    # event that caused this finish action.
    ai_request_start_event_id: str
    ai_metadata: AIFunctionMetadata


@dataclass(kw_only=True, slots=True)
class AIOperationStart(AIEvent):
    pass


@dataclass(kw_only=True, slots=True)
class AIOperationFinish(AIEvent):
    pass
