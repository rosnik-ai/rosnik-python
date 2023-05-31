import logging
import threading
import typing
import queue

from prompthq import api
from prompthq.platforms import openai as phq_openai
from prompthq.types import PromptHqMetadata

logger = logging.getLogger(__name__)

# Define the buffer as a thread-safe queue
event_queue = queue.Queue()

# TODO: support batching
# should probably be by kb size
MAX_BATCH_SIZE = 1

_SERIALIZERS = {"openai": phq_openai.serialize_result}


# Function for capturing data and adding it to the buffer
def capture_data(
    payload: dict,
    response: dict,
    function_fingerprint: typing.List[str],
    start_time: int,
    end_time: int,
    metadata: PromptHqMetadata,
):
    logger.debug("Event enqueued:", payload, function_fingerprint, metadata)
    event_queue.put(
        {
            "request": payload,
            "response": response,
            "function_fingerprint": function_fingerprint,
            "start_time": start_time,
            "end_time": end_time,
            "_prompthq_metadata": metadata,
        }
    )


def process_events(api_key=None):
    logger.debug("Running event processor in thread:", threading.get_ident())
    api_client = api.PromptHqHttpClient(api_key=api_key)
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
