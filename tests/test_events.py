import pytest

from rosnik import config
from rosnik import state
from rosnik.types import core

# Setup the fixture for Event data
@pytest.fixture
def event_data(mocker):
    return {
        "event_type": "test_event",
        "_metadata": mocker.MagicMock()
    }

# Fixture to reset the context after each test to avoid side effects
@pytest.fixture(autouse=True)
def reset_state():
    state._reset()
    yield
    state._reset()

def test_post_init_without_contexts(event_data):
    # Assuming no context is set, no global context should be added.
    event = core.Event(**event_data)
    assert event.context is None

def test_post_init_with_context(event_data):
    # Set a context value using the state management functions
    context = {'key': 'value'}
    state.store(state.State.CONTEXT_ID, context)
    
    event = core.Event(**event_data)
    assert event.context == context

def test_event_context_overrides_stored_and_global(event_data):
    # Set a stored context and a global context hook
    stored_context = {'shared': 'stored', 'unique_stored': 'value_stored'}
    global_context = {'shared': 'global', 'unique_global': 'value_global'}
    event_context = {'shared': 'event', 'unique_event': 'value_event'}
    
    # Simulate setting stored context
    state.store(state.State.CONTEXT_ID, stored_context)
    
    # Simulate a global context hook
    config.Config.event_context_hook = lambda: global_context
    
    # Now create an Event with an event-specific context
    event = core.Event(**event_data, context=event_context)
    
    # The event's context should have 'event' as the 'shared' value
    expected_context = {'shared': 'event', 'unique_global': 'value_global', 'unique_stored': 'value_stored', 'unique_event': 'value_event'}
    assert event.context == expected_context

def test_stored_context_overrides_global(event_data):
    # Set a stored context and a global context hook
    stored_context = {'shared': 'stored', 'unique_stored': 'value_stored'}
    global_context = {'shared': 'global', 'unique_global': 'value_global'}
    
    # Simulate setting stored context
    state.store(state.State.CONTEXT_ID, stored_context)
    
    # Simulate a global context hook
    config.Config.event_context_hook = lambda: global_context
    
    # Now create an Event without an event-specific context
    event = core.Event(**event_data)
    
    # The event's context should have 'stored' as the 'shared' value
    expected_context = {'shared': 'stored', 'unique_global': 'value_global', 'unique_stored': 'value_stored'}
    assert event.context == expected_context

def test_global_context_applied_when_no_other(event_data):
    # Set a global context hook only
    global_context = {'shared': 'global', 'unique_global': 'value_global'}
    
    # Simulate a global context hook
    config.Config.event_context_hook = lambda: global_context
    
    # Now create an Event without an event-specific or stored context
    event = core.Event(**event_data)
    
    # The event's context should be just the global context
    assert event.context == global_context

def test_no_contexts_results_in_none(event_data):
    # Assuming no contexts are set anywhere
    # Simulate a global context hook that returns None
    config.Config.event_context_hook = lambda: None
    
    # Now create an Event without any context
    event = core.Event(**event_data)
    
    # The event's context should be None
    assert event.context is None

def test_post_init_with_journey_id(event_data):
    # Set a journey ID using the state management functions
    journey_id = state.create_journey_id()
    
    event = core.Event(**event_data)
    assert event.journey_id == journey_id

def test_post_init_with_user_interaction_id(event_data):
    # Set a user interaction ID using the state management functions
    user_interaction_id = "interaction_123"
    state.store(state.State.USER_INTERACTION_ID, user_interaction_id)
    
    event = core.Event(**event_data)
    assert event.user_interaction_id == user_interaction_id

def test_post_init_with_device_id(event_data):
    # Set a device ID using the state management functions
    device_id = "device_123"
    state.store(state.State.DEVICE_ID, device_id)
    
    event = core.Event(**event_data)
    assert event.device_id == device_id

def test_post_init_with_all_states(event_data):
    # Set up all states using the state management functions
    context = {'key': 'value'}
    journey_id = state.create_journey_id()
    user_interaction_id = "interaction_123"
    device_id = "device_123"
    
    state.store(state.State.CONTEXT_ID, context)
    state.store(state.State.USER_INTERACTION_ID, user_interaction_id)
    state.store(state.State.DEVICE_ID, device_id)
    
    event = core.Event(**event_data)
    # The event's context should contain the context set up above
    assert event.context == context
    assert event.journey_id == journey_id
    assert event.user_interaction_id == user_interaction_id
    assert event.device_id == device_id
