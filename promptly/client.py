import logging
import threading

from promptly import collector

logger = logging.getLogger(__name__)

openai_enabled = False

try:
    openai_enabled = True
    from promptly.platforms import openai as promptly_openai
except ImportError:
    logger.debug("Skipping OpenAI instrumentation.")


def init(api_key=None):
    if openai_enabled:
        logger.debug("OpenAI is enabled. Patching.")
        promptly_openai._patch_openai()

    # Start the background thread
    thread = threading.Thread(
        target=collector.process_events, kwargs={"api_key": api_key}, daemon=True
    )
    # TODO: handle shutdowns safely
    thread.start()
