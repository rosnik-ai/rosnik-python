from openai import OpenAIError
import pytest
from rosnik import constants

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
def test_completion(
    openai,
    event_queue,
):
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


@pytest.fixture
def mock_openai(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_openai_object(mocker):
    openai_obj = mocker.Mock()
    openai_obj.to_dict_recursive.return_value = {"key": "value"}
    openai_obj.organization = "organization"
    openai_obj.response_ms = 1234
    return openai_obj


def test_response_serializer(mock_openai_object):
    result = openai_.response_serializer(mock_openai_object)
    assert result.response_payload == {"key": "value"}
    assert result.organization == "organization"
    assert result.response_ms == 1234


def test_response_serializer_none():
    assert openai_.response_serializer(None) is None


def test_error_serializer_openai_error():
    error = OpenAIError(
        message='{"error": "details"}',
        json_body={"error": "details"},
        headers={"request-id": "12345", "openai-organization": "test-org"},
        http_status=400,
    )
    result = openai_.error_serializer(error)
    assert result.message == '{"error": "details"}'
    assert result.json_body == {"error": "details"}
    assert result.http_status == 400
    assert result.organization == "test-org"
    assert result.request_id == "12345"


def test_error_serializer_other_exception():
    error = Exception("test exception")
    result = openai_.error_serializer(error)
    assert result.message == "test exception"


def test_patch_completion_already_patched(mock_openai, mocker):
    setattr(mock_openai, f"__test_{constants.NAMESPACE}_patch", True)
    openai_._patch_completion(mock_openai)
    mock_openai.Completion.create.assert_not_called()


def test_patch_chat_completion_already_patched(mock_openai, mocker):
    setattr(mock_openai, f"__test_{constants.NAMESPACE}_patch", True)
    openai_._patch_chat_completion(mock_openai)
    mock_openai.ChatCompletion.create.assert_not_called()


def test_patch_openai_already_patched(mock_openai, mocker):
    setattr(mock_openai, f"__test_{constants.NAMESPACE}_patch", True)
    openai_._patch_openai()
    mock_openai.Completion.assert_not_called()
    mock_openai.ChatCompletion.assert_not_called()
