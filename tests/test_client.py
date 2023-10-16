import rosnik


def test_init(mocker):
    mock_patch = mocker.patch("rosnik.providers.openai._patch_openai")
    mock_logger = mocker.patch("rosnik.client.logger.debug")

    rosnik.init()
    mock_patch.assert_called_once()
    mock_logger.assert_called_once_with("OpenAI is enabled. Patching.")


def test_openai_not_imported(mocker):
    mocker.patch("rosnik.client.openai_enabled", False)
    mock_logger = mocker.patch("rosnik.client.logger.debug")

    rosnik.init()

    mock_logger.assert_called_with("Skipping OpenAI instrumentation.")


def test_sync_mode(mocker):
    mock_logger = mocker.patch("rosnik.client.logger.debug")
    rosnik.init(sync_mode=True)
    mock_logger.assert_called_with("Running in sync mode")


def test_not_sync_mode(mocker):
    mock_logger = mocker.patch("rosnik.client.logger.debug")
    rosnik.init()
    mock_logger.assert_called_once_with("OpenAI is enabled. Patching.")
