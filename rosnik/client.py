import logging

from rosnik import env
from rosnik.events import queue

logger = logging.getLogger(__name__)

openai_enabled = False

try:
    openai_enabled = True
    from rosnik.providers import openai as openai_
except ImportError:
    logger.debug("Skipping OpenAI instrumentation.")


def init():
    if openai_enabled:
        logger.debug("OpenAI is enabled. Patching.")
        openai_._patch_openai()

    if env.is_sync():
        logger.debug("Running in sync mode")
