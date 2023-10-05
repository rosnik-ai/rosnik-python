import os
import sys

import pytest

from rosnik import collector


@pytest.fixture(scope="module")
def vcr_config():
    return {"filter_headers": ["authorization"]}


@pytest.fixture
def openai():
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY", "fake-key")
    # TODO: support organizations
    # openai.organization = openai_organization
    yield openai

    # Reset import state ahead of the next test case
    mods = list(k for k in sys.modules.keys() if k.startswith("openai"))
    for m in mods:
        del sys.modules[m]


@pytest.fixture
def event_queue():
    yield collector.event_queue
    # Clear queue
    while collector.event_queue.qsize() > 0:
        collector.event_queue.get(block=False)
    assert collector.event_queue.qsize() == 0
