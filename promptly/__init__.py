import os

from . import env
from .client import init

__all__ = ["init"]

def auto_init():
    api_key = env.get_api_key()
    if api_key is not None:
        init()

auto_init()