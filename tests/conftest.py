import os
import sys

import pytest


@pytest.fixture(scope="module")
def vcr_config():
    return {"filter_headers": ["authorization"]}


@pytest.fixture
def openai():
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY")
    # TODO: support organizations
    # openai.organization = openai_organization
    yield openai

    # Reset import state ahead of the next test case
    mods = list(k for k in sys.modules.keys() if k.startswith("openai"))
    for m in mods:
        del sys.modules[m]

