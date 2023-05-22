import os

PROMPTHQ_API_KEY = "PROMPTHQ_API_KEY"

def get_api_key():
    return os.environ.get(PROMPTHQ_API_KEY)
