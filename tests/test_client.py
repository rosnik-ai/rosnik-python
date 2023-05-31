import threading


def test_init(mocker):
    mocker.patch("prompthq.platforms.openai._patch_openai")
    mocker.patch("threading.Thread")
    import prompthq

    prompthq.init()
    threading.Thread.assert_called_once()
