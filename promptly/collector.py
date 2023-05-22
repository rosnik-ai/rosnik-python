import json
import threading
import queue

from promptly.platforms import openai as promptly_openai

# Define the buffer as a thread-safe queue
event_queue = queue.Queue()

# TODO: support batching
# should probably be by kb size
MAX_BATCH_SIZE = 1

_SERIALIZERS = {"openai": promptly_openai.serialize_result}


# Function for capturing data and adding it to the buffer
def capture_data(payload, result, function_fingerprint, start_time, end_time, endpoint):
    event_queue.put(
        {
            "request": payload,
            "response": result,
            "function_fingerprint": function_fingerprint,
            "start_time": start_time,
            "end_time": end_time,
            "_endpoint": endpoint,
        }
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


"""Completion API looks like:
Sending: {
    'payload': 
        {'model': 'text-davinci-003',
        'prompt': 'Suggest three names for an animal that is a superhero.\n\nAnimal: Cat\nNames: Captain Sharpclaw, Agent Fluffball, The Incredible Feline\nAnimal: Dog\nNames: Ruff the Protector, Wonder Canine, Sir Barks-a-Lot\nAnimal: Mixed mini poodle\nNames:', 
        'temperature': 0.6}, 
        # TODO: need to convert this to JSON
    'result': <OpenAIObject text_completion id=cmpl-7GvLFZdFXxzQjYWruCGTHowvfU1xO at 0x10b1b7180> JSON: {
  # TODO: what are these?
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "logprobs": null,
      "text": " Wonder Woof, Major Fluff, Super Poodle"
    }
  ],
  "created": 1684268025,
  "id": "cmpl-7GvLFZdFXxzQjYWruCGTHowvfU1xO",
  "model": "text-davinci-003",
  "object": "text_completion",
  "usage": {
    "completion_tokens": 11,
    "prompt_tokens": 65,
    "total_tokens": 76
  }
}, 'function_fingerprint': ['get_stack_frames', 'wrapper', 'index', 'dispatch_request', 'full_dispatch_request', 'wsgi_app']}
"""

"""
{
"prompt": "I want you to act as a resume editor. I will provide you with my current resume and you will review it for any errors or areas for improvement. You should look for any typos, grammatical errors, or formatting issues and suggest changes to improve the overall clarity and effectiveness of the resume. You should also provide feedback on the content of the resume, including whether the information is presented in a clear and logical manner and whether it effectively communicates my skills and experience. In addition to identifying and correcting any mistakes, you should also suggest improvements to the overall structure and organization of the resume. Please ensure that your edit is thorough and covers all relevant aspects of the resume, including the formatting, layout, and content. Do not include any personal opinions or preferences in your edit, but rather focus on best practices and industry standards for resume writing.",
"result": "Sure, I'd be happy to help you with your resume! Please send me the resume so I can begin reviewing it.",
"duration": 1000,
"timestamp": 1620736801000,
"uuid": "8c1a3682-687a-4b23-9ad9-51a86de912ab",
"sessionId": "3f4a5c4d-d3e6-4f87-bd55-982754a61981",
"spanName": "resume-intro",
"userId": "ebc9c3e1-9e25-4f39-af51-1e8c5f9f3f9c"
}

# This is the way
customer.runpromptly.com/api/v1/ingest/openai/completion
{
"data": data,
}
"""


def send_event(event):
    print("Sending:", json.dumps(event))
