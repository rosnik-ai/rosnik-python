import threading
from promptly import collector

openai_enabled = False

try:
    openai_enabled = True
    from promptly.platforms import openai as promptly_openai
except ImportError:
    print("Skipping openai instrumentation.")


def init(api_key):
    if openai_enabled:
        promptly_openai._patch_openai()

    # Start the background thread
    thread = threading.Thread(target=collector.process_events, daemon=True)
    # TODO: handle shutdowns safely
    thread.start()
