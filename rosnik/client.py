import logging
import warnings

from rosnik import config

logger = logging.getLogger(__name__)

openai_enabled = False

try:
    from rosnik.providers import openai as openai_

    openai_enabled = True
except ImportError:
    pass


def init(api_key=None, sync_mode=None, environment=None):
    config.Config.api_key = api_key
    config.Config.sync_mode = sync_mode
    config.Config.environment = environment

    if config.Config.api_key is None:
        warnings.warn("`api_key` is not set and an API token was not provided on init")

    if openai_enabled:
        logger.debug("OpenAI is enabled. Patching.")
        openai_._patch_openai()
    else:
        logger.debug("Skipping OpenAI instrumentation.")

    if config.Config.sync_mode:
        logger.debug("Running in sync mode")
