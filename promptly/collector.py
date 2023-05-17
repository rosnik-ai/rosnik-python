import threading
import time
import queue

# Define the buffer as a thread-safe queue
event_queue = queue.Queue()

# TODO: support batching
MAX_BATCH_SIZE = 1


# Function for capturing data and adding it to the buffer
def capture_data(payload, result, function_fingerprint):
    event_queue.put(
        {"payload": payload, "result": result, "function_fingerprint": function_fingerprint}
    )


def process_events():
    print("Running event processor in thread:", threading.get_ident())
    batch = []
    while True:
        # Wait for events to be available in the queue
        event = event_queue.get()
        send_event(event)

        # TODO: implement batching server-side
        # Add the event to the batch
        # batch.append(event)

        # If the batch size reaches the maximum, process and send it
        # if len(batch) >= MAX_BATCH_SIZE:
        # process_and_send_batch(batch)
        # batch = []


def send_event(event):
    print("Sending:", event)
