import os

API_KEY = "ROSNIK_API_KEY"


def get_api_key():
    return os.environ.get(API_KEY)
