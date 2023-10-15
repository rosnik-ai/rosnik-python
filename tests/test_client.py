from rosnik.events import queue


def test_init(mocker):
    mocker.patch("rosnik.providers.openai._patch_openai")
    mocker.patch("rosnik.events.queue.start_event_processor")
    import rosnik

    rosnik.init()
    queue.start_event_processor.assert_called_once()