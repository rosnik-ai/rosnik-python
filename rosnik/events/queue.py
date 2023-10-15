import contextvars
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

        # TODO: support batching
        self.MAX_BATCH_SIZE = 1

    def run(self):
        self.started = True
        self.process_events()

    def process_events(self):
        while True:
            # Wait for events to be available in the queue
            logger.debug(f"Queue size: {self.event_queue.qsize()}. In PID: {os.getpid()}. In thread: {threading.get_ident()}")
            logger.debug(f"Waiting for an event in the queue. In PID: {os.getpid()}. In thread: {threading.get_ident()}")
            event = self.event_queue.get()
            logger.debug(f"Sending event {event.event_id} in PID {os.getpid()} in thread {threading.get_ident()}.")
            self.api_client.send_event(event)

            # TODO: implement batching server-side
            # Add the event to the batch
            # batch.append(event)

            # If the batch size reaches the maximum, process and send it
            # if len(batch) >= self.MAX_BATCH_SIZE:
            #     self.process_and_send_batch(batch)
            # batch = []

    def flush_events(self, send_events=True):
        logger.debug("Flushing event queue with size: %s", self.event_queue.qsize())
        while self.event_queue.qsize() > 0:
            event = self.event_queue.get()
            if send_events:
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
    logger.debug(f"Event processor {event_processor} in PID {os.getpid()}")
    # If we're sending events in the background, start this thread.
    if event_processor is None:
        logger.debug(f"Event processor is None in PID {os.getpid()}. Starting a new one.")
        event_processor = EventProcessor(event_queue, api_client)
        event_processor.start()

    try:
        logger.debug(f"Enqueuing event in queue mode: {event.event_id}. In PID: {os.getpid()}. In thread: {threading.get_ident()}")
        event_queue.put(event, block=False)
        logger.debug(f"Queue size after enqueue: {event_queue.qsize()}. In PID: {os.getpid()}. In thread: {threading.get_ident()}")
    except queue.Full:
        # TODO: what do we do here?
        logger.warning("rosnik events queue is full")