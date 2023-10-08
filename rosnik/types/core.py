import time
import os
import platform
from dataclasses import dataclass
from typing import List, Optional


@dataclass(kw_only=True, slots=True)
class StaticMetadata:
    environment: Optional[str] = os.environ.get("ROSNIK_ENVIRONMENT", None)
    runtime: str = platform.python_implementation()
    runtime_version: str = platform.python_version()
    # TODO: how to sync pyproject version to this
    sdk_version: str = "0.0.8"


@dataclass(kw_only=True, slots=True)
class Metadata(StaticMetadata):
    function_fingerprint: List[str]


@dataclass(kw_only=True, slots=True)
class Event:
    event_type: str
    # Epoch
    journey_id: int = 123
    # Epoch
    sent_at: int = int(time.time())
    # Epoch unless not set, which will be -1
    occurred_at: Optional[int] = None
    # JSONable user defined context
    # TODO: Supplied via either @context or with context({})
    context: Optional[dict] = None
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
