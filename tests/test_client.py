import threading


def test_init(mocker):
    mocker.patch("promptly.platforms.openai._patch_openai")
    mocker.patch("threading.Thread")
    import promptly

    promptly.init()
    threading.Thread.assert_called_once()
