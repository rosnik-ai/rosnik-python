import os

NAMESPACE = "ROSNIK"
API_KEY = f"{NAMESPACE}_API_KEY"
# If set to a non-0 value,
# we will send values synchronously.
SYNC = f"{NAMESPACE}_SYNC"


def get_api_key():
    return os.environ.get(API_KEY)


def is_sync():
    sync = os.environ.get(SYNC)
    return sync is not None and sync != "0"
