import threading


def test_init(mocker):
    mocker.patch("prompthq.platforms.openai._patch_openai")
    mocker.patch("threading.Thread")
    import prompthq

    prompthq.init()
    threading.Thread.assert_called_once()

def test_track_feedback_simple(mocker):
    mocker.patch("prompthq.collector.enqueue_feedback")
    mocker.patch("threading.Thread")
    import prompthq

    prompthq.track_feedback("cmpl-123", "user-123", 10, comment="Whoa this is cool")
    prompthq.collector.enqueue_feedback.assert_called_once_with("cmpl-123", "user-123", 10, comment="Whoa this is cool")