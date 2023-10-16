import time
import os
import platform
from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin
import ulid

from rosnik import state


def _generate_event_id():
    return ulid.new().str


@dataclass(kw_only=True, slots=True)
class StaticMetadata:
    environment: Optional[str] = os.environ.get("ROSNIK_ENVIRONMENT", None)
    runtime: str = platform.python_implementation()
    runtime_version: str = platform.python_version()
    # TODO: how to sync pyproject version to this
    sdk_version: str = "0.0.22"


@dataclass(kw_only=True, slots=True)
class Metadata(StaticMetadata):
    function_fingerprint: str


@dataclass(kw_only=True, slots=True)
class Event(DataClassJsonMixin):
    # Unique event ID
    event_id: str = field(default_factory=_generate_event_id)
    event_type: str
    journey_id: str = field(default_factory=state.get_journey_id)
    # Epoch in ms
    sent_at: int = int(time.time_ns() / 1000000)
    # Epoch unless not set, which will be -1
    occurred_at: Optional[int] = None
    # JSONable user defined context
    # TODO: TBD on how this is provided.
    context: Optional[dict] = None
    # Users could be part of an AI event or a User event
    user_id: Optional[str] = None
    device_id: Optional[str] = field(default_factory=state.get_device_id)
    # Our own metadata
    _metadata: Metadata
    # User Interaction ID: this is the causal user.interaction.track
    # event ID for this event. If it's unset then something else
    # we're not tracking caused this action.
    user_interaction_id: Optional[str] = field(default_factory=state.get_user_interaction_id)


@dataclass(kw_only=True, slots=True)
class AIEvent(Event):
    # model name
    ai_model: str
    # openai
    ai_provider: str
    # AI action: completion, chatcompletion
    ai_action: str


class UserEvent(Event):
    # JSONable user properties that can be added
    user_properties: dict
