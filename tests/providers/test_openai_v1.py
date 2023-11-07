import os
import pytest
from rosnik import constants

from rosnik.providers import openai_v1 as openai_
from rosnik.types.ai import (
    AIFunctionMetadata,
    AIRequestFinish,
    AIRequestStart,
    AIRequestStartStream,
)
from rosnik.types.core import Metadata

try:
    from openai.types.completion import Completion
except ImportError:
    # Tests are skipped if on a lower version of OpenAI
    pass


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

    if openai.__version__[0] == "0":
        pytest.skip("Skipping tests for OpenAI SDK v1")


@pytest.fixture
def azure_openai_client(openai):
    expected_api_base = "https://rosnik.openai.azure.com"
    expected_api_version = "2023-05-15"
    return openai.AzureOpenAI(
        api_key=os.environ.get("AZURE_API_KEY", "test-key"),
        azure_endpoint=expected_api_base,
        api_version=expected_api_version,
    )


@pytest.fixture
def azure_openai_chat_completions_class(azure_openai_client):
    cls = azure_openai_client.chat.completions.__class__
    original_create = cls.create
    yield cls
    cls.create = original_create


@pytest.mark.vcr
def test_completion(
    openai_client,
    openai_completions_class,
    event_queue,
):
    openai_._patch_completion(openai_completions_class)
    assert event_queue.qsize() == 0
    openai_client.completions.create(
        model="text-davinci-003",
        prompt=generate_prompt("Mixed mini poodle"),
        temperature=0.6,
    )
    assert event_queue.qsize() == 2
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert request_start.ai_metadata.openai_attributes.api_type == "openai"
    assert request_start.ai_metadata.openai_attributes.api_version is None
    assert request_start._metadata.stream is False

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert request_finish.ai_metadata.openai_attributes.api_type == "openai"
    assert request_finish.ai_metadata.openai_attributes.api_version is None
    assert request_finish._metadata.stream is False


@pytest.mark.vcr
def test_chat_completion(openai_client, openai_chat_completions_class, event_queue):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    openai_._patch_chat_completion(openai_chat_completions_class)
    assert event_queue.qsize() == 0
    openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
    )
    assert event_queue.qsize() == 2
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert request_start.ai_metadata.openai_attributes.api_type == "openai"
    assert request_start.ai_metadata.openai_attributes.api_version is None
    assert request_start._metadata.stream is False

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert request_finish.ai_metadata.openai_attributes.api_type == "openai"
    assert request_finish.ai_metadata.openai_attributes.api_version is None
    assert request_finish._metadata.stream is False


@pytest.mark.vcr
def test_chat_completion__with_user(openai_client, openai_chat_completions_class, event_queue):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    openai_._patch_chat_completion(openai_chat_completions_class)
    assert event_queue.qsize() == 0
    openai_client.chat.completions.create(
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


# Skip the test if running in CI since there seems
# to be an issue with pytest-recording and streaming.
@pytest.mark.skipif(os.environ.get("CI") == "true", reason="CI doesn't support streaming")
def test_chat_completion__streaming(openai_client, openai_chat_completions_class, event_queue):
    system_prompt = """
    You are an aspiring edm artist.
    Generate a song using words, for example "uhn tiss uhn tiss", that give the impression of an edm song.
    Your inspiration is the artist provided by the user.
    """  # noqa
    input_text = "Daft Punk"
    openai_._patch_chat_completion(openai_chat_completions_class)
    assert event_queue.qsize() == 0
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
        stream=True,
    )

    expected_completion = ""
    for line in response:
        s = line.choices[0].delta.content
        if isinstance(s, str):
            expected_completion += s

    assert event_queue.qsize() == 3
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert request_start.ai_metadata.openai_attributes.api_type == "openai"
    assert request_start.ai_metadata.openai_attributes.api_version is None
    assert request_start._metadata.stream is True

    first_chunk_event: AIRequestStartStream = event_queue.get()
    assert first_chunk_event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert first_chunk_event.ai_metadata.openai_attributes.api_type == "openai"
    assert first_chunk_event.ai_metadata.openai_attributes.api_version is None
    assert first_chunk_event.response_ms == first_chunk_event.sent_at - request_start.sent_at
    assert first_chunk_event.ai_request_start_event_id == request_start.event_id
    assert first_chunk_event.ai_model == request_start.ai_model
    assert first_chunk_event.ai_provider == openai_._OAI
    assert first_chunk_event.ai_action == "chat.completions"
    assert first_chunk_event.response_payload is None
    assert first_chunk_event._metadata.stream is True

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert request_finish.ai_metadata.openai_attributes.api_type == "openai"
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
@pytest.mark.openai_azure
def test_chat_completion__azure(
    azure_openai_client, azure_openai_chat_completions_class, event_queue
):
    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"

    openai_._patch_chat_completion(azure_openai_chat_completions_class)

    assert event_queue.qsize() == 0
    azure_openai_client.chat.completions.create(
        model="gpt-35-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
    )

    expected_api_base = "https://rosnik.openai.azure.com/openai/"
    expected_api_version = "2023-05-15"
    assert event_queue.qsize() == 2
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == expected_api_base
    assert request_start.ai_metadata.openai_attributes.api_type == "azureopenai"
    assert request_start.ai_metadata.openai_attributes.api_version == expected_api_version

    request_finish: AIRequestFinish = event_queue.get()
    assert request_finish.ai_metadata.openai_attributes.api_base == expected_api_base
    assert request_finish.ai_metadata.openai_attributes.api_type == "azureopenai"
    assert request_finish.ai_metadata.openai_attributes.api_version == expected_api_version


@pytest.mark.skipif(os.environ.get("CI") == "true", reason="CI doesn't support streaming")
@pytest.mark.openai_azure
def test_chat_completion__streaming__azure(
    azure_openai_client, azure_openai_chat_completions_class, event_queue
):
    system_prompt = """
    You are an aspiring edm artist.
    Generate a song using words, for example "uhn tiss uhn tiss", that give the impression of an edm song.
    Your inspiration is the artist provided by the user.
    """  # noqa
    input_text = "Daft Punk"

    openai_._patch_chat_completion(azure_openai_chat_completions_class)
    assert event_queue.qsize() == 0
    response = azure_openai_client.chat.completions.create(
        model="gpt-35-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
        stream=True,
    )

    expected_completion = ""
    for line in response:
        s = line.choices[0].delta.content
        if isinstance(s, str):
            expected_completion += s

    expected_api_base = "https://rosnik.openai.azure.com/openai/"
    expected_api_version = "2023-05-15"
    assert event_queue.qsize() == 3
    request_start: AIRequestStart = event_queue.get()
    assert request_start.ai_metadata.openai_attributes.api_base == expected_api_base
    assert request_start.ai_metadata.openai_attributes.api_type == "azureopenai"
    assert request_start.ai_metadata.openai_attributes.api_version == expected_api_version
    assert request_start._metadata.stream is True

    first_chunk_event: AIRequestStartStream = event_queue.get()
    assert first_chunk_event.ai_metadata.openai_attributes.api_base == expected_api_base
    assert first_chunk_event.ai_metadata.openai_attributes.api_type == "azureopenai"
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
    assert request_finish.ai_metadata.openai_attributes.api_type == "azureopenai"
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
def test_error(openai, openai_client, openai_chat_completions_class, event_queue):
    system_prompt = "You are a helpful assistant." * 100000
    input_text = "What is a dog?"
    openai_._patch_chat_completion(openai_chat_completions_class)
    assert event_queue.qsize() == 0
    with pytest.raises(openai.RateLimitError):
        openai_client.chat.completions.create(
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
        == "Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 1 / min. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}"  # noqa
    )
    assert event.error_data.json_body == {
        "error": {
            "code": "rate_limit_exceeded",
            "message": "Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 1 / min. Visit https://platform.openai.com/account/rate-limits to learn more.",
            "param": None,
            "type": "tokens",
        }
    }
    assert event.error_data.headers == {
        "cf-cache-status": "DYNAMIC",
        "cf-ray": "8220890f4fde237a-SJC",
        "connection": "keep-alive",
        "content-length": "342",
        "content-type": "application/json; charset=utf-8",
        "date": "Mon, 06 Nov 2023 21:47:32 GMT",
        "server": "cloudflare",
        "alt-svc": 'h3=":443"; ma=86400',
        "strict-transport-security": "max-age=15724800; includeSubDomains",
        "vary": "Origin",
        "x-ratelimit-limit-requests": "3500",
        "x-ratelimit-limit-tokens": "90000",
        "x-ratelimit-remaining-requests": "3499",
        "x-ratelimit-remaining-tokens": "89999",
        "x-ratelimit-reset-requests": "17ms",
        "x-ratelimit-reset-tokens": "0s",
        "x-request-id": "22294aa187021e2d4d2f75c2419b3364",
    }
    # If it's set on the module we will pick that up
    # as a part of openai_attributes.
    assert event.error_data.organization is None
    assert event.error_data.request_id == "22294aa187021e2d4d2f75c2419b3364"
    assert event.error_data.http_status == 429
    assert (
        event.error_data.http_body
        == '{\n    "error": {\n        "message": "Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 1 / min. Visit https://platform.openai.com/account/rate-limits to learn more.",\n        "type": "tokens",\n        "param": null,\n        "code": "rate_limit_exceeded"\n    }\n}\n'  # noqa
    )
    assert (
        event.error_data.user_message
        == "Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-3.5-turbo in organization org-b9yq2nxMHc4y6yjvJ7n6qLpe on tokens per min. Limit: 90000 / min. Current: 1 / min. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}"  # noqa
    )
    assert event.error_data.code is None


def test_request_hook_valid_payload(mocker):
    result = openai_.request_hook(
        {"model": "test_model"},
        "test_function_fingerprint",
        generate_metadata=lambda: AIFunctionMetadata(
            ai_provider=openai_._OAI, ai_action="completions"
        ),
        instance=mocker.Mock(),
    )

    assert result.ai_model == "test_model"
    assert result.ai_provider == openai_._OAI
    assert result.ai_action == "completions"


def test_response_hook_valid_payload(mocker, openai_client):
    prior_event = AIRequestStart(
        ai_model="test_model",
        ai_provider=openai_._OAI,
        ai_action="completions",
        ai_metadata=AIFunctionMetadata(ai_provider=openai_._OAI, ai_action="completions"),
        request_payload={"model": "test_model"},
        user_id="test_user",
        _metadata=Metadata(function_fingerprint="test_function_fingerprint"),
    )

    completions_response = Completion(
        id="test_id",
        object="test_object",
        created=123,
        model="model_value",
        choices=[],
    )
    result = openai_.response_hook(
        completions_response,
        "test_function_fingerprint",
        prior_event,
        generate_metadata=lambda: AIFunctionMetadata(
            ai_provider=openai_._OAI, ai_action="completions"
        ),
        instance=mocker.Mock(_client=openai_client),
    )

    assert result.ai_model == "model_value"
    assert result.ai_provider == openai_._OAI
    assert result.ai_action == "completions"


def test_error_hook_valid_error(mocker):
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
        instance=mocker.Mock(),
    )

    assert result.error_data.message == "test exception"


@pytest.fixture
def mock_openai(mocker):
    return mocker.Mock()


def test_patch_completion_already_patched(mock_openai):
    setattr(mock_openai, f"__{constants.NAMESPACE}_patch", True)
    openai_._patch_completion(mock_openai)
    mock_openai.completions.assert_not_called()


def test_patch_chat_completion_already_patched(mock_openai):
    setattr(mock_openai, f"__{constants.NAMESPACE}_patch", True)
    openai_._patch_chat_completion(mock_openai)
    mock_openai.chat.completions.assert_not_called()


def test_patch_openai_already_patched(mock_openai):
    setattr(mock_openai, f"__{constants.NAMESPACE}_patch", True)
    openai_.patch()
    mock_openai.completions.assert_not_called()
    mock_openai.chat.completions.assert_not_called()


@pytest.mark.vcr
@pytest.mark.openai_azure
def test_multiple_clients(openai_client, azure_openai_client, event_queue):
    """More of an e2e test. We want to make sure we track
    the right information based on the client used, even
    if multiple are used in one process.
    """
    openai_.patch()
    openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a world class poet."},
            {"role": "user", "content": "Write a poem about dogs in space."},
        ],
    )

    azure_openai_client.chat.completions.create(
        model="gpt-35-turbo",
        messages=[
            {"role": "system", "content": "You are a world class songwriter."},
            {"role": "user", "content": "Write a verse about dogs on the moon."},
        ],
    )

    assert event_queue.qsize() == 4
    # First 2 are openai
    event = event_queue.get()
    assert event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert event.ai_metadata.openai_attributes.api_type == "openai"
    assert event.ai_metadata.openai_attributes.api_version is None
    event = event_queue.get()
    assert event.ai_metadata.openai_attributes.api_base == "https://api.openai.com/v1/"
    assert event.ai_metadata.openai_attributes.api_type == "openai"
    assert event.ai_metadata.openai_attributes.api_version is None

    # Second 2 are azureopenai
    event = event_queue.get()
    expected_api_base = "https://rosnik.openai.azure.com/openai/"
    expected_api_version = "2023-05-15"
    assert event.ai_metadata.openai_attributes.api_base == expected_api_base
    assert event.ai_metadata.openai_attributes.api_type == "azureopenai"
    assert event.ai_metadata.openai_attributes.api_version == expected_api_version
    event = event_queue.get()
    assert event.ai_metadata.openai_attributes.api_base == expected_api_base
    assert event.ai_metadata.openai_attributes.api_type == "azureopenai"
    assert event.ai_metadata.openai_attributes.api_version == expected_api_version
