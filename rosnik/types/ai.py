from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin


from rosnik.types.core import AIEvent


@dataclass(kw_only=True, slots=True)
class OpenAIAttributes(DataClassJsonMixin):
    api_base: str
    api_type: str
    api_version: str
    organization: Optional[str] = None
    # OpenAI tracks response ms
    response_ms: Optional[int] = None


@dataclass(kw_only=True, slots=True)
class ResponseData(DataClassJsonMixin):
    response_payload: dict
    organization: str
    response_ms: int
    openai_attributes: OpenAIAttributes


@dataclass(kw_only=True, slots=True)
class ErrorResponseData(DataClassJsonMixin):
    message: str
    json_body: Optional[str] = None
    headers: Optional[dict] = None
    http_status: Optional[int] = None
    organization: Optional[str] = None
    request_id: Optional[str] = None
    http_body: Optional[str] = None
    user_message: Optional[str] = None
    code: Optional[str] = None


@dataclass(kw_only=True, slots=True)
class AIFunctionMetadata(DataClassJsonMixin):
    ai_provider: str
    ai_action: str
    openai_attributes: Optional[OpenAIAttributes] = None


@dataclass(kw_only=True, slots=True)
class AIRequestStart(AIEvent):
    event_type: str = "ai.request.start"
    # JSONable request payload / kwargs sent through the SDK
    request_payload: dict
    ai_metadata: AIFunctionMetadata
    ai_request_start_event_id: Optional[str] = None

    def __post_init__(self):
        AIEvent.__post_init__(self)
        self.ai_request_start_event_id = self.event_id


@dataclass(kw_only=True, slots=True)
class AIRequestFinish(AIEvent):
    event_type: str = "ai.request.finish"
    # JSONable response payload/body
    # null on errors
    response_payload: Optional[dict] = None
    # This is the Event ID of the ai.request.start
    # event that caused this finish action.
    ai_request_start_event_id: str
    ai_metadata: AIFunctionMetadata
    # Null on error
    # Our client-side calculation of duration
    response_ms: int
    # null on success
    error_data: Optional[ErrorResponseData] = None


@dataclass(kw_only=True, slots=True)
class AIRequestStartStream(AIRequestFinish):
    """One-off event used to track first-byte time."""

    event_type: str = "ai.request.start.stream"


@dataclass(kw_only=True, slots=True)
class AIOperationStart(AIEvent):
    pass


@dataclass(kw_only=True, slots=True)
class AIOperationFinish(AIEvent):
    pass
