import logging
from contextvars import ContextVar
from typing import Optional

logger = logging.getLogger(__name__)

user_interaction_id_cv: ContextVar[Optional[str]] = ContextVar("user_interaction_id")


def get_interaction_id():
    return user_interaction_id_cv.get(None)


def set_interaction_id(interaction_id: str):
    existing_id = user_interaction_id_cv.get(None)
    if existing_id:
        logger.warning(f"Overwriting user interaction ID from {existing_id} to {interaction_id}")
    user_interaction_id_cv.set(interaction_id)
