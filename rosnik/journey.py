import logging
from contextvars import ContextVar
from typing import Optional

from ulid import monotonic as ulid

logger = logging.getLogger(__name__)

journey_id_cv: ContextVar[Optional[str]] = ContextVar("journey_id")

# TODO: turn into a config or smth
JOURNEY_TIMEOUT = 30 * 60  # 30 minutes

def get_journey_id():
    return journey_id_cv.get(None)

def get_or_create_journey_id():
    _new_id = ulid.new()
    new_id_str = _new_id.str
    now_from_new_id = int(_new_id.timestamp().timestamp)
    existing_journey_id = get_journey_id()
    # If we don't have one, make one.
    if existing_journey_id is None:
        set_journey_id(new_id_str)
        # TODO: this needs to be sent to the frontend
        return new_id_str

    # If we have one, and it's stale, then make a new one.
    existing_journey_ulid = ulid.parse(existing_journey_id)
    existing_timestamp = existing_journey_ulid.timestamp().timestamp
    if existing_journey_id and now_from_new_id - existing_timestamp > JOURNEY_TIMEOUT:
        set_journey_id(new_id_str)
        # TODO: this needs to be sent to the frontend
        return new_id_str

    # Otherwise the one we have works.
    # TODO: this needs to be sent to the frontend.
    return existing_journey_id


def set_journey_id(journey_id: str):
    existing_journey_id = get_journey_id()
    if existing_journey_id:
        logger.warning(f"Overwriting journey ID from {existing_journey_id} to {journey_id}")
    journey_id_cv.set(journey_id)