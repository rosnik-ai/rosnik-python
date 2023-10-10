import logging
import threading

from rosnik import env
from rosnik.events import queue

logger = logging.getLogger(__name__)

openai_enabled = False

try:
    openai_enabled = True
    from rosnik.providers import openai as phq_openai
except ImportError:
    logger.debug("Skipping OpenAI instrumentation.")


def init():
    if openai_enabled:
        logger.debug("OpenAI is enabled. Patching.")
        phq_openai._patch_openai()

    if not env.is_sync():
        logger.debug("Running event processor in separate thread")
        # Start the background thread
        thread = threading.Thread(target=queue.process_events, daemon=True)
        # TODO: handle shutdowns safely
        thread.start()
