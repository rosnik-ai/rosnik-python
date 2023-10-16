import os
import pytest
from rosnik import constants

from rosnik.providers import openai as openai_
from rosnik.types.ai import AIFunctionMetadata, AIRequestFinish, AIRequestStart
from rosnik.types.core import Metadata


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
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert request_start.ai_metadata.openai_attributes.api_type == "open_ai"
    assert request_start.ai_metadata.openai_attributes.api_version is None

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert request_finish.ai_metadata.openai_attributes.api_type == "open_ai"
    assert request_finish.ai_metadata.openai_attributes.api_version is None


@pytest.mark.vcr
def test_chat_completion__azure(openai, event_queue):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"

    expected_api_base = "https://rosnik.openai.azure.com/"
    expected_api_type = "azure"
    expected_api_version = "2023-05-15"
    openai.api_key = os.environ.get("AZURE_API_KEY")
    openai.api_base = expected_api_base
    openai.api_type = expected_api_type
    openai.api_version = expected_api_version
    openai_._patch_chat_completion(openai)

    assert event_queue.qsize() == 0
    openai.ChatCompletion.create(
        deployment_id="gpt-35-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
    )
    assert event_queue.qsize() == 2
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == expected_api_base
    assert request_start.ai_metadata.openai_attributes.api_type == expected_api_type
    assert request_start.ai_metadata.openai_attributes.api_version == expected_api_version

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == expected_api_base
    assert request_finish.ai_metadata.openai_attributes.api_type == expected_api_type
    assert request_finish.ai_metadata.openai_attributes.api_version == expected_api_version


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
    openai_obj.get.return_value = "model_value"
    return openai_obj


def test_request_serializer_valid_payload():
    result = openai_.request_serializer(
        {"model": "test_model"},
        "test_function_fingerprint",
        generate_metadata=lambda: AIFunctionMetadata(
            ai_provider=openai_._OAI, ai_action="completions"
        ),
    )

    assert result.ai_model == "test_model"
    assert result.ai_provider == openai_._OAI
    assert result.ai_action == "completions"


def test_response_serializer_valid_payload(mock_openai_object):
    prior_event = AIRequestStart(
        ai_model="test_model",
        ai_provider=openai_._OAI,
        ai_action="completions",
        ai_metadata=AIFunctionMetadata(ai_provider=openai_._OAI, ai_action="completions"),
        request_payload={"model": "test_model"},
        user_id="test_user",
        _metadata=Metadata(function_fingerprint="test_function_fingerprint"),
    )

    result = openai_.response_serializer(
        mock_openai_object,
        "test_function_fingerprint",
        prior_event,
        generate_metadata=lambda: AIFunctionMetadata(
            ai_provider=openai_._OAI, ai_action="completions"
        ),
    )

    assert result.ai_model == "model_value"
    assert result.ai_provider == openai_._OAI
    assert result.ai_action == "completions"


def test_error_serializer_valid_error():
    prior_event = AIRequestStart(
        ai_model="test_model",
        ai_provider=openai_._OAI,
        ai_action="completions",
        ai_metadata=AIFunctionMetadata(ai_provider=openai_._OAI, ai_action="completions"),
        request_payload={"model": "test_model"},
        user_id="test_user",
        _metadata=Metadata(function_fingerprint="test_function_fingerprint"),
    )

    error = Exception("test exception")
    result = openai_.error_serializer(
        error,
        "test_function_fingerprint",
        prior_event,
        generate_metadata=lambda: AIFunctionMetadata(
            ai_provider=openai_._OAI, ai_action="completions"
        ),
    )

    assert result.error_data.message == "test exception"


def test_patch_completion_already_patched(mock_openai):
    setattr(mock_openai, f"__{constants.NAMESPACE}_patch", True)
    openai_._patch_completion(mock_openai)
    mock_openai.Completion.create.assert_not_called()


def test_patch_chat_completion_already_patched(mock_openai):
    setattr(mock_openai, f"__{constants.NAMESPACE}_patch", True)
    openai_._patch_chat_completion(mock_openai)
    mock_openai.ChatCompletion.create.assert_not_called()


def test_patch_openai_already_patched(mock_openai):
    setattr(mock_openai, f"__{constants.NAMESPACE}_patch", True)
    openai_._patch_openai()
    mock_openai.Completion.assert_not_called()
    mock_openai.ChatCompletion.assert_not_called()
