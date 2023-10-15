from rosnik import state


def test_store_and_retrieve():
    state.store(state.State.JOURNEY_ID, "test_journey")
    assert state.retrieve(state.State.JOURNEY_ID) == "test_journey"

    state.store(state.State.USER_INTERACTION_ID, "test_interaction")
    assert state.retrieve(state.State.USER_INTERACTION_ID) == "test_interaction"

    state.store(state.State.DEVICE_ID, "test_device")
    assert state.retrieve(state.State.DEVICE_ID) == "test_device"


def test_create_journey_id():
    journey_id = state.create_journey_id()
    assert journey_id is not None
    assert state.retrieve(state.State.JOURNEY_ID) == journey_id


def test_get_journey_id():
    state._reset()
    journey_id1 = state.get_journey_id()
    assert journey_id1 is not None

    journey_id2 = state.get_journey_id()
    assert journey_id2 == journey_id1


def test_get_device_id():
    state._reset()
    assert state.get_device_id() is None

    state.store(state.State.DEVICE_ID, "test_device")
    assert state.get_device_id() == "test_device"


def test_get_user_interaction_id():
    state._reset()
    assert state.get_user_interaction_id() is None

    state.store(state.State.USER_INTERACTION_ID, "test_interaction")
    assert state.get_user_interaction_id() == "test_interaction"


def test_reset():
    state.store(state.State.JOURNEY_ID, "test_journey")
    state.store(state.State.USER_INTERACTION_ID, "test_interaction")
    state.store(state.State.DEVICE_ID, "test_device")

    state._reset()

    assert state.retrieve(state.State.JOURNEY_ID) is None
    assert state.retrieve(state.State.USER_INTERACTION_ID) is None
    assert state.retrieve(state.State.DEVICE_ID) is None
