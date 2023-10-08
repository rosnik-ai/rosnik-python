from dataclasses import dataclass, field
from typing import List, Optional, TypedDict


class Metadata(TypedDict):
    platform: str
    action: str
    environment: str
    lang: str


class PromptHqEvent(TypedDict):
    request: dict
    response: dict
    function_fingerprint: List[str]
    start_time: int
    end_time: int
    _metadata: Metadata

@dataclass(kw_only=True, slots=True)
class Event:
    event_type: str = field(kw_only=True)
    # Epoch
    journey_id: int
    # Epoch
    sent_at: int
    # Epoch unless not set, which will be -1
    occurred_at: Optional[int] = field(default=None)
    # JSONable user defined context
    context: Optional[dict] = field(default=None)
    # Our own metadata
    _metadata: Metadata

@dataclass(kw_only=True, slots=True)
class AIEvent(Event):
    model: str
    provider: str

class UserEvent(Event):
    user_id: str
    # JSONable user properties that can be added
    user_properties: dict
