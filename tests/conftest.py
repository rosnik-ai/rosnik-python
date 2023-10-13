import os
import sys

import pytest

from rosnik.events import queue


@pytest.fixture(scope="module")
def vcr_config():
    return {"filter_headers": ["authorization"]}


@pytest.fixture
def openai():
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY", "fake-key")
    yield openai

    # Reset import state ahead of the next test case
    mods = list(k for k in sys.modules.keys() if k.startswith("openai"))
    for m in mods:
        del sys.modules[m]


@pytest.fixture
def event_queue():
    yield queue.event_queue
    # Clear queue
    while queue.event_queue.qsize() > 0:
        queue.event_queue.get(block=False)
    assert queue.event_queue.qsize() == 0
