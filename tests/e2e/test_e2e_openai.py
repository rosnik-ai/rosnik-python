import pytest
import prompthq
from prompthq import collector
from prompthq.platforms import openai as phq_openai


@pytest.mark.vcr
def test_e2e_chat_completion(mocker, openai, event_queue):
    # e2e-ish
    mocker.patch("prompthq.api.PromptHqHttpClient._post")

    system_prompt = "You are a helpful assistant."
    input_text = "What is a dog?"
    fake_user_id = "fake-user-123"
    phq_openai._patch_chat_completion(openai)
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
        user=fake_user_id,
    )
    assert event_queue.qsize() == 1
    prompthq.track_feedback(
        completion_id=result.id,
        user_id=fake_user_id,
        score=10,
        metadata={"comment": "Great feature!"},
    )
    assert event_queue.qsize() == 2
    collector._flush_events()
    assert event_queue.qsize() == 0