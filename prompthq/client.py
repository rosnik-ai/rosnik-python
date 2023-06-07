import logging
import threading

from prompthq import collector

logger = logging.getLogger(__name__)

openai_enabled = False

try:
    openai_enabled = True
    from prompthq.platforms import openai as phq_openai
except ImportError:
    logger.debug("Skipping OpenAI instrumentation.")


def init(api_key=None):
    if openai_enabled:
        logger.debug("OpenAI is enabled. Patching.")
        phq_openai._patch_openai()

    # Start the background thread
    thread = threading.Thread(
        target=collector.process_events, kwargs={"api_key": api_key}, daemon=True
    )
    # TODO: handle shutdowns safely
    thread.start()


def track_feedback(
    completion_id: str = None, user_id: str = None, score: int = None, metadata: dict = None
):
    return collector.enqueue_feedback(
        completion_id=completion_id, user_id=user_id, score=score, metadata=metadata
    )
