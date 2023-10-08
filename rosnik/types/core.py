import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(kw_only=True, slots=True)
class StaticMetadata:
    environment: Optional[str] = os.environ.get("ROSNIK_ENVIRONMENT", None)
    runtime: str = "python"
    runtime_version: str = '.'.join([str(_) for _ in sys.version_info[:3]])
    # TODO: how to sync pyproject version to this
    sdk_version: str = '0.0.8'

@dataclass(kw_only=True, slots=True)
class Metadata(StaticMetadata):
    function_fingerprint: List[str]

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
    # TODO: Supplied via either @context or with context({})
    context: Optional[dict] = field(default=None)
    # Our own metadata
    _metadata: Metadata

@dataclass(kw_only=True, slots=True)
class AIEvent(Event):
    # model name
    ai_model: str
    # openai
    ai_provider: str
    # AI action: completion, chatcompletion
    ai_action: str

class UserEvent(Event):
    user_id: str
    # JSONable user properties that can be added
    user_properties: dict
