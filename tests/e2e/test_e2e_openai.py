import pytest
from rosnik.events import queue
from rosnik.providers import openai as phq_openai
from rosnik.types.ai import AIRequestFinish, AIRequestStart


@pytest.mark.vcr
def test_e2e_chat_completion(mocker, openai, event_queue):
    # e2e-ish
    mocker.patch("rosnik.api.IngestClient._post")

    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    fake_user_id = "fake-user-123"
    phq_openai._patch_chat_completion(openai)
    expected_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]
    openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=expected_messages,
        user=fake_user_id,
    )
    assert event_queue.qsize() == 2
    request_event: AIRequestStart = event_queue.get()
    assert isinstance(request_event, AIRequestStart)
    assert request_event.journey_id is not None
    assert request_event.ai_action == "chat.completions"
    assert request_event.ai_model == "gpt-3.5-turbo"
    assert request_event.ai_provider == "openai"
    assert request_event.request_payload["messages"] == expected_messages
    assert request_event.user_interaction_id is None
    response_event: AIRequestFinish = event_queue.get()
    assert isinstance(response_event, AIRequestFinish)
    assert response_event.journey_id == request_event.journey_id
    assert response_event.ai_action == "chat.completions"
    # TODO: figure out we handle this in the data view
    assert response_event.ai_model == "gpt-3.5-turbo-0613"
    assert response_event.ai_provider == "openai"
    assert response_event.ai_request_start_event_id == request_event.event_id

    # rosnik.track_feedback(
    #     completion_id=result.id,
    #     user_id=fake_user_id,
    #     score=10,
    #     metadata={"comment": "Great feature!"},
    # )
    # assert event_queue.qsize() == 2
    queue._flush_events(send_events=False)
    assert event_queue.qsize() == 0
