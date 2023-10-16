import sys

import pytest

from rosnik import config
from rosnik.events import queue


@pytest.fixture(scope="module")
def vcr_config():
    return {"filter_headers": ["authorization"]}


@pytest.fixture
def openai():
    import openai

    yield openai

    # Reset import state ahead of the next test case
    mods = list(k for k in sys.modules.keys() if k.startswith("openai"))
    for m in mods:
        del sys.modules[m]

@pytest.fixture(autouse=True)
def config_reset():
    yield
    config.Config = config._Config()

@pytest.fixture
def event_queue(mocker):
    # Don't send process the event queue so we can inspect
    # it in tests.
    mocker.patch("rosnik.events.queue.EventProcessor")
    yield queue.event_queue
    # Clear queue
    while queue.event_queue.qsize() > 0:
        queue.event_queue.get(block=False)
    assert queue.event_queue.qsize() == 0
