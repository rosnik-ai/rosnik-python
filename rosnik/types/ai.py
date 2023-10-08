from dataclasses import field, dataclass
from rosnik.types.core import AIEvent

@dataclass(kw_only=True, slots=True)
class AIRequestStart(AIEvent):
    event_type: str = 'ai.request.start'
    # JSONable request payload
    request_payload: dict

@dataclass(kw_only=True, slots=True)
class AIRequestFinish(AIEvent):
    event_type: str = 'ai.request.finish'
    # JSONable response payload/body
    response_payload: dict

@dataclass(kw_only=True, slots=True)
class AIOperationStart(AIEvent):
    pass

@dataclass(kw_only=True, slots=True)
class AIOperationFinish(AIEvent):
    pass