import logging
import threading
import queue

from rosnik import api
from rosnik import env
from rosnik.types.core import Event

logger = logging.getLogger(__name__)

# Define the buffer as a thread-safe queue
event_queue = queue.Queue()

# TODO: support batching
# should probably be by kb size
MAX_BATCH_SIZE = 1

api_client = api.IngestClient()


def enqueue_event(event: Event):
    if env.is_sync():
        api_client.send_event(event)
        return

    try:
        event_queue.put(event, block=False)
    except queue.Full:
        # TODO: what do we do here?
        logger.warning("rosnik events queue is full")


def process_events():
    logger.debug("Running event processor in thread: %s", threading.get_ident())
    while True:
        # Wait for events to be available in the queue
        event = event_queue.get()
        api_client.send_event(event)

        # TODO: implement batching server-side
        # Add the event to the batch
        # batch.append(event)

        # If the batch size reaches the maximum, process and send it
        # if len(batch) >= MAX_BATCH_SIZE:
        # process_and_send_batch(batch)
        # batch = []


def _flush_events(send_events=True):
    logger.debug("Flushing event queue with size: %s", event_queue.qsize())
    api_client = api.IngestClient()
    while event_queue.qsize() > 0:
        event = event_queue.get()
        if send_events:
            api_client.send_event(event)
