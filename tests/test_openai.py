import os
import pytest
from rosnik import constants

from rosnik.providers import openai as openai_
from rosnik.types.ai import (
    AIFunctionMetadata,
    AIRequestFinish,
    AIRequestStartStream,
    AIRequestStart,
)
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


@pytest.fixture(autouse=True)
def skip_pre_v1():
    import openai

    if openai.__version__[0] == "1":
        pytest.skip("Skipping tests for OpenAI SDK pre-v1")


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
    assert request_start._metadata.stream is False

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert request_finish.ai_metadata.openai_attributes.api_type == "open_ai"
    assert request_finish.ai_metadata.openai_attributes.api_version is None
    assert request_finish._metadata.stream is False


@pytest.mark.vcr
def test_chat_completion__with_user(openai, event_queue):
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
        user="test-user",
    )
    assert event_queue.qsize() == 2
    request_start: AIRequestStart = event_queue.get()
    assert request_start.user_id == "test-user"

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.user_id == "test-user"


@pytest.mark.vcr
def test_chat_completion__streaming(openai, event_queue):
    system_prompt = """
    You are an aspiring edm artist. 
    Generate a song using words, for example "uhn tiss uhn tiss", that give the impression of an edm song.
    Your inspiration is the artist provided by the user.
    """  # noqa
    input_text = "Daft Punk"
    openai_._patch_chat_completion(openai)
    assert event_queue.qsize() == 0
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
        stream=True,
    )

    expected_completion = ""
    for line in response:
        s = line["choices"][0].get("delta", {}).get("content")
        if isinstance(s, str):
            expected_completion += s

    assert event_queue.qsize() == 3
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert request_start.ai_metadata.openai_attributes.api_type == "open_ai"
    assert request_start.ai_metadata.openai_attributes.api_version is None
    assert request_start._metadata.stream is True

    first_chunk_event: AIRequestStartStream = event_queue.get()
    assert first_chunk_event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert first_chunk_event.ai_metadata.openai_attributes.api_type == "open_ai"
    assert first_chunk_event.ai_metadata.openai_attributes.api_version is None
    assert first_chunk_event.response_ms == first_chunk_event.sent_at - request_start.sent_at
    assert first_chunk_event.ai_request_start_event_id == request_start.event_id
    assert first_chunk_event.ai_model == request_start.ai_model
    assert first_chunk_event.ai_provider == openai_._OAI
    assert first_chunk_event.ai_action == "chat.completions"
    assert first_chunk_event.response_payload is None
    assert first_chunk_event._metadata.stream is True

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1"
    assert request_finish.ai_metadata.openai_attributes.api_type == "open_ai"
    assert request_finish.ai_metadata.openai_attributes.api_version is None
    assert request_finish.response_ms == request_finish.sent_at - request_start.sent_at
    assert request_finish.ai_request_start_event_id == request_start.event_id
    # Iterations know the more specific model.
    assert request_finish.ai_model == "gpt-3.5-turbo-0613"
    assert request_finish.ai_provider == openai_._OAI
    assert request_finish.ai_action == "chat.completions"
    assert request_finish._metadata.stream is True
    streamed_completion = request_finish.response_payload["choices"][0]["message"]["content"]
    assert streamed_completion == expected_completion


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
def test_chat_completion__azure__engine(openai, event_queue):
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
        engine="gpt-35-turbo",
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
def test_chat_completion__streaming__azure(openai, event_queue):
    system_prompt = """
    You are an aspiring edm artist. 
    Generate a song using words, for example "uhn tiss uhn tiss", that give the impression of an edm song.
    Your inspiration is the artist provided by the user.
    """  # noqa
    input_text = "Daft Punk"
    expected_api_base = "https://rosnik.openai.azure.com/"
    expected_api_type = "azure"
    expected_api_version = "2023-05-15"
    openai.api_key = os.environ.get("AZURE_API_KEY")
    openai.api_base = expected_api_base
    openai.api_type = expected_api_type
    openai.api_version = expected_api_version
    openai_._patch_chat_completion(openai)
    assert event_queue.qsize() == 0
    response = openai.ChatCompletion.create(
        deployment_id="gpt-35-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
        stream=True,
    )

    expected_completion = ""
    for line in response:
        s = line["choices"][0].get("delta", {}).get("content")
        if isinstance(s, str):
            expected_completion += s

    assert event_queue.qsize() == 3
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == expected_api_base
    assert request_start.ai_metadata.openai_attributes.api_type == expected_api_type
    assert request_start.ai_metadata.openai_attributes.api_version == expected_api_version
    assert request_start._metadata.stream is True

    first_chunk_event: AIRequestStartStream = event_queue.get()
    assert first_chunk_event.ai_metadata.openai_attributes.api_base == expected_api_base
    assert first_chunk_event.ai_metadata.openai_attributes.api_type == expected_api_type
    assert first_chunk_event.ai_metadata.openai_attributes.api_version == expected_api_version
    assert first_chunk_event.response_ms == first_chunk_event.sent_at - request_start.sent_at
    assert first_chunk_event.ai_request_start_event_id == request_start.event_id
    assert first_chunk_event.ai_model == request_start.ai_model
    assert first_chunk_event.ai_provider == openai_._OAI
    assert first_chunk_event.ai_action == "chat.completions"
    assert first_chunk_event.response_payload is None
    assert first_chunk_event._metadata.stream is True

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == expected_api_base
    assert request_finish.ai_metadata.openai_attributes.api_type == expected_api_type
    assert request_finish.ai_metadata.openai_attributes.api_version == expected_api_version
    assert request_finish.response_ms == request_finish.sent_at - request_start.sent_at
    assert request_finish.ai_request_start_event_id == request_start.event_id
    # Iterations know the more specific model.
    assert request_finish.ai_model == "gpt-35-turbo"
    assert request_finish.ai_provider == openai_._OAI
    assert request_finish.ai_action == "chat.completions"
    assert request_finish._metadata.stream is True
    streamed_completion = request_finish.response_payload["choices"][0]["message"]["content"]
    assert streamed_completion == expected_completion


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
    assert isinstance(event_queue.get(), AIRequestStart)
    event: AIRequestFinish = event_queue.get()
    assert isinstance(event, AIRequestFinish)
    assert (
        event.error_data.message
        == "Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 0 / min. Contact us through our help center at help.openai.com if you continue to have issues."  # noqa
    )
    assert event.error_data.json_body == {
        "error": {
            "message": "Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 0 / min. Contact us through our help center at help.openai.com if you continue to have issues.",  # noqa
            "type": "tokens",
            "param": None,
            "code": "rate_limit_exceeded",
        }
    }
    assert event.error_data.headers == {
        "CF-Cache-Status": "DYNAMIC",
        "CF-RAY": "8163762d4dc42513-SJC",
        "Connection": "keep-alive",
        "Content-Length": "359",
        "Content-Type": "application/json; charset=utf-8",
        "Date": "Sat, 14 Oct 2023 23:04:30 GMT",
        "Server": "cloudflare",
        "alt-svc": 'h3=":443"; ma=86400',
        "strict-transport-security": "max-age=15724800; includeSubDomains",
        "vary": "Origin",
        "x-ratelimit-limit-requests": "3500",
        "x-ratelimit-limit-tokens": "90000",
        "x-ratelimit-remaining-requests": "3499",
        "x-ratelimit-remaining-tokens": "90000",
        "x-ratelimit-reset-requests": "17ms",
        "x-ratelimit-reset-tokens": "0s",
        "x-request-id": "df4093761753468e57c467fd3774f9ad",
    }
    # If it's set on the module we will pick that up
    # as a part of openai_attributes.
    assert event.error_data.organization is None
    assert event.error_data.request_id is None
    assert event.error_data.http_status == 429
    assert (
        event.error_data.http_body
        == '{\n    "error": {\n        "message": "Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 0 / min. Contact us through our help center at help.openai.com if you continue to have issues.",\n        "type": "tokens",\n        "param": null,\n        "code": "rate_limit_exceeded"\n    }\n}\n'  # noqa
    )
    assert (
        event.error_data.user_message
        == "Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 0 / min. Contact us through our help center at help.openai.com if you continue to have issues."  # noqa
    )
    assert event.error_data.code is None


@pytest.fixture
def mock_openai(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_openai_object(mocker):
    openai_obj = mocker.Mock()
    openai_obj.get.return_value = "model_value"
    return openai_obj


def test_request_hook_valid_payload():
    result = openai_.request_hook(
        {"model": "test_model"},
        "test_function_fingerprint",
        generate_metadata=lambda: AIFunctionMetadata(
            ai_provider=openai_._OAI, ai_action="completions"
        ),
    )

    assert result.ai_model == "test_model"
    assert result.ai_provider == openai_._OAI
    assert result.ai_action == "completions"


def test_response_hook_valid_payload(mock_openai_object):
    prior_event = AIRequestStart(
        ai_model="test_model",
        ai_provider=openai_._OAI,
        ai_action="completions",
        ai_metadata=AIFunctionMetadata(ai_provider=openai_._OAI, ai_action="completions"),
        request_payload={"model": "test_model"},
        user_id="test_user",
        _metadata=Metadata(function_fingerprint="test_function_fingerprint"),
    )

    result = openai_.response_hook(
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


def test_error_hook_valid_error():
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
    result = openai_.error_hook(
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
