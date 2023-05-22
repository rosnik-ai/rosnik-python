import os
import sys

import pytest

from promptly.platforms import openai as promptly_openai


def generate_prompt(animal):
    return """Suggest three names for an animal that is a superhero.

Animal: Cat
Names: Captain Sharpclaw, Agent Fluffball, The Incredible Feline
Animal: Dog
Names: Ruff the Protector, Wonder Canine, Sir Barks-a-Lot
Animal: {}
Names:""".format(
        animal.capitalize()
    )


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


@pytest.mark.vcr
def test_completion(openai):
    promptly_openai._patch_completion(openai)
    openai.Completion.create(
        model="text-davinci-003",
        prompt=generate_prompt("Mixed mini poodle"),
        temperature=0.6,
    )


@pytest.mark.vcr
def test_chat_completion(openai):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    promptly_openai._patch_chat_completion(openai)
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
    )
