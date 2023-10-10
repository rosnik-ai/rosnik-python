from contextvars import ContextVar
from typing import Optional

from ulid import monotonic as ulid

journey_id_cv: ContextVar[Optional[str]] = ContextVar("journey_id")

# TODO: turn into a config or smth
JOURNEY_TIMEOUT = 30 * 60  # 30 minutes


def get_or_create_journey_id():
    _new_id = ulid.new()
    new_id_str = _new_id.str
    now_from_new_id = int(_new_id.timestamp().timestamp)
    existing_journey_id = journey_id_cv.get(None)
    # If we don't have one, make one.
    if existing_journey_id is None:
        journey_id_cv.set(new_id_str)
        # TODO: this needs to be sent to the frontend
        return new_id_str

    # If we have one, and it's stale, then make a new one.
    existing_journey_ulid = ulid.parse(existing_journey_id)
    existing_timestamp = existing_journey_ulid.timestamp().timestamp
    if existing_journey_id and now_from_new_id - existing_timestamp > JOURNEY_TIMEOUT:
        journey_id_cv.set(new_id_str)
        # TODO: this needs to be sent to the frontend
        return new_id_str

    # Otherwise the one we have works.
    # TODO: this needs to be sent to the frontend.
    return existing_journey_id
