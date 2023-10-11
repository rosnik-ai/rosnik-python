from dataclasses import dataclass
from typing import Optional
from rosnik.types.core import UserEvent


@dataclass(kw_only=True, slots=True)
class UserGoalSuccess(UserEvent):
    event_type: str = "user.goal.success"
    # TODO: should this be goal ID
    # that needs to be configured
    # in the product first?
    goal_name: str


# TODO: do we need this?
@dataclass(kw_only=True, slots=True)
class UserJourneyStart(UserEvent):
    """Fired if we generate a new Journey ID."""
    event_type: str = "user.journey.start"


@dataclass(kw_only=True, slots=True)
class UserInteractionTrack(UserEvent):
    event_type: str = "user.interaction.track"
    # One of: ai-request, text-edit
    interaction_type: str

@dataclass(kw_only=True, slots=True)
class UserFeedbackTrack(UserEvent):
    """Explicit feedback"""
    event_type: str = "user.feedback.track"
    score: Optional[int]
    open_response: Optional[str]
