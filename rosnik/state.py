"""
A request on its own can be considered a journey,
if there is not an external journey ID supplied.

We manage state here across the 3 values we care about.
Outside of Journey ID, they can be set to None, which
would mean they are user-less journeys.
"""
from enum import Enum
import logging
from contextvars import ContextVar
from typing import Optional

import ulid

logger = logging.getLogger(__name__)

_journey_id_key = "journey_id"
_user_interaction_id_key = "user_interaction_id"
_device_id_key = "device_id"

journey_id_cv: ContextVar[Optional[str]] = ContextVar(_journey_id_key)
user_interaction_id_cv: ContextVar[Optional[str]] = ContextVar(_user_interaction_id_key)
device_id_cv: ContextVar[Optional[str]] = ContextVar(_device_id_key)


class State(Enum):
    JOURNEY_ID = _journey_id_key
    USER_INTERACTION_ID = _user_interaction_id_key
    DEVICE_ID = _device_id_key


_state = {
    State.JOURNEY_ID: journey_id_cv,
    State.USER_INTERACTION_ID: user_interaction_id_cv,
    State.DEVICE_ID: device_id_cv,
}


def store(state_type: State, value: str):
    _state[state_type].set(value)


def retrieve(state_type: State):
    return _state[state_type].get(None)


def create_journey_id():
    journey_id = ulid.new().str
    store(State.JOURNEY_ID, journey_id)
    return journey_id


def get_journey_id():
    journey_id = retrieve(State.JOURNEY_ID)
    if journey_id is None:
        return create_journey_id()
    return journey_id


def get_device_id():
    return retrieve(State.DEVICE_ID)


def get_user_interaction_id():
    return retrieve(State.USER_INTERACTION_ID)


def _reset():
    journey_id_cv.set(None)
    user_interaction_id_cv.set(None)
    device_id_cv.set(None)
