import pytest
import requests
import responses
from rosnik.api import IngestClient, _base_url, _retry_status_code
from rosnik.env import API_KEY
from rosnik.types.core import Event, Metadata

@pytest.fixture
def mock_event():
    return Event(event_type="test.event", event_id="123456", journey_id="journey_123", _metadata=Metadata(function_fingerprint=""))

def test_no_api_key_set(mocker):
    # Mock env.get_api_key to return None
    mocker.patch("rosnik.env.get_api_key", return_value=None)
    
    client = IngestClient()
    assert client.api_key is None

def test_send_event_successful(mocker, mock_event):
    # Mock API response
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mocker.patch.object(IngestClient, "_post", return_value=mock_response)
    
    # Mock env.get_api_key to return a fake API key
    mocker.patch("rosnik.env.get_api_key", return_value="fake_api_key")

    client = IngestClient()
    client.send_event(mock_event)
    IngestClient._post.assert_called_once_with(_base_url, headers=client.headers, json=mock_event.to_dict())

def test_send_event_http_error(mocker, mock_event):
    mock_logger = mocker.patch("rosnik.api.logger.warning")
    # Mock an HTTPError
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("An error occurred")
    
    # Now, mock _post to return this mock_response
    mocker.patch.object(IngestClient, "_post", return_value=mock_response)
    # Mock env.get_api_key to return a fake API key
    mocker.patch("rosnik.env.get_api_key", return_value="fake_api_key")

    client = IngestClient()
    client.send_event(mock_event)
    mock_logger.assert_called_once_with("Failed to send event: An error occurred")

@pytest.mark.parametrize("status_code", _retry_status_code)
@responses.activate
def test_retry_adapter(mocker, status_code):
    mock_logger = mocker.patch("rosnik.api.logger.warning")
    mock_event = Event(event_type="test-event", event_id="1", journey_id="j-1", _metadata=Metadata(function_fingerprint=""))
    test_url = "https://ingest.rosnik.ai/api/v1/events"

    # A counter to track the number of retries
    retry_count = {"count": 0}

    # A callback to simulate server errors
    def request_callback(request):
        retry_count["count"] += 1
        return (status_code, {}, "Bad Gateway")

    # Setting up the mock response
    responses.add_callback(
        responses.POST, test_url,
        callback=request_callback,
        content_type='application/json',
    )

    client = IngestClient()
    client.send_event(mock_event)
    assert mock_logger.call_count == 1
    assert "Failed to send event after 3 attempts:" in mock_logger.call_args_list[0][0][0]
    assert retry_count["count"] == 4