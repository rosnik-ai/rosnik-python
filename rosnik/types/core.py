import time
import os
import platform
from dataclasses import dataclass, field
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin
from ulid import monotonic as ulid

from rosnik import journey


def _generate_event_id():
    return ulid.new().str


@dataclass(kw_only=True, slots=True)
class StaticMetadata:
    environment: Optional[str] = os.environ.get("ROSNIK_ENVIRONMENT", None)
    runtime: str = platform.python_implementation()
    runtime_version: str = platform.python_version()
    # TODO: how to sync pyproject version to this
    sdk_version: str = "0.0.13"


@dataclass(kw_only=True, slots=True)
class Metadata(StaticMetadata):
    function_fingerprint: List[str]


@dataclass(kw_only=True, slots=True)
class Event(DataClassJsonMixin):
    # Unique event ID
    event_id: str = field(default_factory=_generate_event_id)
    event_type: str
    # Epoch
    journey_id: str = field(default_factory=journey.get_or_create_journey_id)
    # Epoch
    sent_at: int = int(time.time())
    # Epoch unless not set, which will be -1
    occurred_at: Optional[int] = None
    # JSONable user defined context
    # TODO: Supplied via either @context or with context({})?
    context: Optional[dict] = None
    # Users could be part of an AI event or a User event
    user_id: Optional[str] = None
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
    # User Interaction ID: this is the causal user.interaction.track
    # event ID for this AI request. If it's unset then something else
    # we're not tracking caused this action.
    user_interaction_id: Optional[str] = None


class UserEvent(Event):
    # JSONable user properties that can be added
    user_properties: dict
