import logging
import rosnik


def test_init(mocker, debug_logger):
    mock_patch = mocker.patch("rosnik.providers.openai._patch_openai")

    rosnik.init()
    mock_patch.assert_called_once()
    messages = [record.message for record in debug_logger.records]
    "OpenAI is enabled. Patching." in messages


def test_openai_not_imported(debug_logger, mocker):
    mocker.patch("rosnik.client.openai_enabled", False)

    rosnik.init()

    messages = [record.message for record in debug_logger.records]
    "Skipping OpenAI instrumentation." in messages


def test_sync_mode(debug_logger):
    rosnik.init(sync_mode=True)
    messages = [record.message for record in debug_logger.records]
    "Running in sync mode" in messages


def test_not_sync_mode(debug_logger):
    rosnik.init()
    messages = [record.message for record in debug_logger.records]
    "OpenAI is enabled. Patching." in messages


def test_api_key_sync_mode_and_environment_assignment(mocker):
    mock_api_key = "TEST_API_KEY"
    mock_sync_mode = True
    mock_environment = "TEST_ENVIRONMENT"

    rosnik.init(api_key=mock_api_key, sync_mode=mock_sync_mode, environment=mock_environment)

    assert rosnik.config.Config.api_key == mock_api_key
    assert rosnik.config.Config.sync_mode == mock_sync_mode
    assert rosnik.config.Config.environment == mock_environment


def test_openai_enabled_and_sync_mode(caplog, mocker):
    caplog.set_level(logging.DEBUG)
    mock_patch = mocker.patch("rosnik.providers.openai._patch_openai")

    rosnik.init(sync_mode=True)

    mock_patch.assert_called_once()
    messages = [record.message for record in caplog.records]
    "OpenAI is enabled. Patching." in messages
    "Running in sync mode" in messages
