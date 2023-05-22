import inspect
import logging
import sys
import time

logger = logging.getLogger(__name__)

from promptly import collector


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


def wrap_class_method(wrapped_func, prompthq_metadata):
    def wrapper(*args, **kwargs):
        logger.debug("Prep for ingest request:", kwargs)
        start_time = time.time()
        result = wrapped_func(*args, **kwargs)
        end_time = time.time()
        logger.debug("Send to ingest response:", result)

        limited_frames = get_stack_frames(5)
        calling_functions = [frame.f_code.co_name for frame in limited_frames]
        collector.capture_data(
            kwargs, result, calling_functions, start_time, end_time, prompthq_metadata
        )
        return result

    return wrapper
