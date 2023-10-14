import pytest

from rosnik.providers import openai as openai_


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
def test_completion(openai, event_queue):
    openai_._patch_completion(openai)
    assert event_queue.qsize() == 0
    openai.Completion.create(
        model="text-davinci-003",
        prompt=generate_prompt("Mixed mini poodle"),
        temperature=0.6,
    )
    assert event_queue.qsize() == 2


@pytest.mark.vcr
def test_chat_completion(openai, event_queue):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    openai_._patch_chat_completion(openai)
    assert event_queue.qsize() == 0
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
    )
    assert event_queue.qsize() == 2

@pytest.mark.vcr
def test_error(openai, event_queue):
    system_prompt = "You are a helpful assistant." * 100000
    input_text = "What is a dog?"
    openai_._patch_chat_completion(openai)
    assert event_queue.qsize() == 0
    with pytest.raises(openai.error.RateLimitError):
        openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ],
        )
    assert event_queue.qsize() == 2
