import logging
import threading
import queue
import os

from rosnik import api
from rosnik import env
from rosnik.types.core import Event

logger = logging.getLogger(__name__)


class EventProcessor(threading.Thread):
    def __init__(self, queue: queue.Queue, api_client: api.IngestClient):
        super().__init__()
        self.daemon = True
        self.started = False
        self.event_queue = queue
        self.api_client = api_client
        self.pid = os.getpid()

    def run(self):
        self.started = True
        self.process_events()

    def process_events(self):
        while True:
            event = self.event_queue.get()
            self.api_client.send_event(event)


event_queue = queue.Queue()
api_client = api.IngestClient()
event_processor = None


def enqueue_event(event: Event):
    if env.is_sync():
        logger.debug(f"Enqueuing event in sync mode: {event.event_id}")
        api_client.send_event(event)
        return

    global event_processor
    # If we're sending events in the background, start this thread.
    if event_processor is None:
        logger.debug("Event processor is None. Starting a new one.")
        event_processor = EventProcessor(event_queue, api_client)
        event_processor.start()

    try:
        logger.debug(f"Enqueuing event {event.event_id}")
        event_queue.put(event, block=False)
    except queue.Full:
        logger.warning("rosnik events queue is full")
