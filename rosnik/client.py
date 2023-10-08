import logging
import threading

from rosnik.events import queue

logger = logging.getLogger(__name__)

openai_enabled = False

try:
    openai_enabled = True
    from rosnik.providers import openai as phq_openai
except ImportError:
    logger.debug("Skipping OpenAI instrumentation.")


def init(api_key=None):
    if openai_enabled:
        logger.debug("OpenAI is enabled. Patching.")
        phq_openai._patch_openai()

    # Start the background thread
    thread = threading.Thread(
        target=queue.process_events, kwargs={"api_key": api_key}, daemon=True
    )
    # TODO: handle shutdowns safely
    thread.start()


# def track_feedback(
#     completion_id: str = None, user_id: str = None, score: int = None, metadata: dict = None
# ):
#     return queue.enqueue_feedback(
#         completion_id=completion_id, user_id=user_id, score=score, metadata=metadata
#     )
