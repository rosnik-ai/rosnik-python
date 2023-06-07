import threading


def test_init(mocker):
    mocker.patch("prompthq.platforms.openai._patch_openai")
    mocker.patch("threading.Thread")
    import prompthq

    prompthq.init()
    threading.Thread.assert_called_once()


def test_track_feedback_simple(mocker):
    mocker.patch("prompthq.collector.enqueue_feedback", return_value=True)
    mocker.patch("threading.Thread")
    import prompthq

    result = prompthq.track_feedback(
        completion_id="cmpl-123",
        user_id="user-123",
        score=10,
        metadata={"comment": "Great feature!"},
    )
    assert result is True
    prompthq.collector.enqueue_feedback.assert_called_once_with(
        completion_id="cmpl-123",
        user_id="user-123",
        score=10,
        metadata={"comment": "Great feature!"},
    )
