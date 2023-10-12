from typing import Optional
from rosnik.types.user import UserFeedbackTrack, UserInteractionTrack
from rosnik.events import queue


def track_user_interaction(user_id: str, interaction_type: str):
    event = UserInteractionTrack(user_id=user_id, interaction_type=interaction_type)
    queue.enqueue_event(event)
    return event


def track_user_feedback(
    user_id: str, score: Optional[int] = None, open_response: Optional[str] = None
):
    event = UserFeedbackTrack(user_id=user_id, score=score, open_response=open_response)
    queue.enqueue_event(event)
    return event
