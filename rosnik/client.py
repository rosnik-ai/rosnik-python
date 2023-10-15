import logging

from rosnik import env

logger = logging.getLogger(__name__)

openai_enabled = False

try:
    openai_enabled = True
    from rosnik.providers import openai as openai_
except ImportError:
    pass


def init():
    if openai_enabled:
        logger.debug("OpenAI is enabled. Patching.")
        openai_._patch_openai()
    else:
        logger.debug("Skipping OpenAI instrumentation.")

    if env.is_sync():
        logger.debug("Running in sync mode")
