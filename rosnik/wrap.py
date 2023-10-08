import inspect
import logging
import sys
from typing import Callable

from rosnik.events import ai
from rosnik.types.ai import AIFunctionMetadata

logger = logging.getLogger(__name__)


def get_stack_frames(num, useGetFrame=True):
    """Quickly get stack frames via:
    https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116
    """
    # Not all versions of python have the sys._getframe() method.
    # All should have inspect, though it is really slow
    if useGetFrame and hasattr(sys, "_getframe"):
        frame = sys._getframe(0)
        frames = [frame]

        while frame.f_back is not None and len(frames) <= num:
            frames.append(frame.f_back)
            frame = frame.f_back

        return frames
    else:
        return inspect.stack()[:num]


# TODO: will need more wrappers.
# TODO: I think I need a trick here to rename `wrapper` to `wrapped_func` s
# datadog and other tracing libs don't record the wrong thing.
def wrap_class_method(wrapped_func: Callable, metadata: AIFunctionMetadata):
    def wrapper(*args, **kwargs):
        logger.debug("Prep for ingest request:", kwargs)
        # TODO: profile this.
        limited_frames = get_stack_frames(5)
        # Flatten into a period separated sequence so we can do function chain search later.
        calling_functions = ".".join([frame.f_code.co_name for frame in limited_frames])

        # TODO: support stream
        request_id = ai.track_request_start(kwargs, metadata, calling_functions)
        result = wrapped_func(*args, **kwargs)
        ai.track_request_finish(result, metadata, calling_functions, request_id)

        return result

    return wrapper