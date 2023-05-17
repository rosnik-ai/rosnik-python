import os

import pytest

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

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

@pytest.mark.vcr
def test_completion():
    response = openai.Completion.create(
                model="text-davinci-003",
                prompt=generate_prompt("Mixed mini poodle"),
                temperature=0.6,
            )