import logging
import warnings
from contextlib import contextmanager

from rosnik import config, state
from rosnik.providers import openai as openai_
from rosnik.providers import openai_v1 as openai_v1_


logger = logging.getLogger(__name__)


def init(api_key=None, sync_mode=None, environment=None, event_context_hook=None):
    config.Config.api_key = api_key
    config.Config.sync_mode = sync_mode
    config.Config.environment = environment
    config.Config.event_context_hook = event_context_hook

    if config.Config.api_key is None:
        warnings.warn("`api_key` is not set and an API token was not provided on init")

    try:
        logger.debug("OpenAI pre-v1 is enabled. Patching.")
        openai_._patch_openai()
    except ImportError:
        logger.debug("Skipping OpenAI instrumentation.")

    try:
        logger.debug("OpenAI v1 is enabled. Patching.")
        openai_v1_.patch()
    except ImportError:
        logger.debug("Skipping OpenAI instrumentation.")

    if config.Config.sync_mode:
        logger.debug("Running in sync mode")


@contextmanager
def context(prompt_name: str = None, **kwargs):
    """Set context for the events sent within this context manager."""
    token = state.store(state.State.CONTEXT_ID, {"prompt_name": prompt_name, **kwargs})
    yield
    state.reset_context(token)
