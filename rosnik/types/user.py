from dataclasses import dataclass
from rosnik.types.core import UserEvent

@dataclass(kw_only=True, slots=True)
class UserGoalSuccess(UserEvent):
    event_type: str = 'user.goal.success'
    # TODO: should this be goal ID
    # that needs to be configured
    # in the product first?
    goal_name: str

@dataclass(kw_only=True, slots=True)
class UserJourneyStart(UserEvent):
    """Fired if we generate a new Journey ID."""
    event_type: str = 'user.journey.start'

@dataclass(kw_only=True, slots=True)
class UserInteractionTrack(UserEvent):
    event_type: str = 'user.interaction.track'

@dataclass(kw_only=True, slots=True)
class UserFeedbackTrack(UserEvent):
    """Explicit feedback"""
    event_type: str = 'user.feedback.track'