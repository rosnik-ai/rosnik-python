import logging
import time
import platform
from dataclasses import dataclass, field
from typing import Callable, Optional

from dataclasses_json import DataClassJsonMixin
import ulid

from rosnik import config
from rosnik import state

logger = logging.getLogger(__name__)


def _generate_event_id():
    return ulid.new().str


@dataclass(kw_only=True, slots=True)
class StaticMetadata:
    environment: Optional[str] = field(default_factory=lambda: config.Config.environment)
    runtime: str = platform.python_implementation()
    runtime_version: str = platform.python_version()
    # TODO: how to sync pyproject version to this
    sdk_version: str = "0.0.34"


@dataclass(kw_only=True, slots=True)
class Metadata(StaticMetadata):
    function_fingerprint: str
    stream: bool = False


_reserved_words = ["environment"]


@dataclass(kw_only=True, slots=True)
class Event(DataClassJsonMixin):
    # Unique event ID
    event_id: str = field(default_factory=_generate_event_id)
    event_type: str
    journey_id: str = field(default_factory=state.get_journey_id)
    # Epoch in ms
    sent_at: int = field(default_factory=lambda: int(time.time_ns() / 1000000))
    # Epoch unless not set, which will be -1
    occurred_at: Optional[int] = None
    # JSONable user defined context
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

    def __post_init__(self):
        if not isinstance(config.Config.event_context_hook, Callable):
            return

        try:
            self.context = config.Config.event_context_hook()
            context_env = self.context.pop("environment", None)
            if context_env:
                self._metadata.environment = context_env
        except Exception:
            logger.exception(
                f"Could not generate context from {config.Config.event_context_hook.__name__}"
            )


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
