import inspect
import logging
import sys
from typing import Callable


from rosnik.events import ai
from rosnik.types.ai import AIFunctionMetadata

import wrapt

logger = logging.getLogger(__name__)


def get_stack_frames(num, use_get_frame=True):
    """Quickly get stack frames via:
    https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116
    """
    # Not all versions of python have the sys._getframe() method.
    # All should have inspect, though it is really slow
    if use_get_frame and hasattr(sys, "_getframe"):
        frame = sys._getframe(0)
        frames = [frame]

        while frame.f_back is not None and len(frames) < num:
            frames.append(frame.f_back)
            frame = frame.f_back

        return frames
    else:
        return inspect.stack()[:num]


def wrap_class_method(
    klass,
    method_name: str,
    metadata: AIFunctionMetadata,
    response_serializer: Callable,
    error_serializer: Callable,
):
    def wrapper(wrapped, instance, args, kwargs):
        limited_frames = get_stack_frames(5)
        # Flatten into a period separated sequence so we can do function chain search later.
        calling_functions = ".".join([frame.f_code.co_name for frame in limited_frames])

        # TODO: support streaming.
        request_event = ai.track_request_start(kwargs, metadata, calling_functions)
        try:
            result = wrapped(*args, **kwargs)
        except Exception as e:
            ai.track_request_finish(
                None,
                metadata,
                calling_functions,
                request_event,
                response_serializer,
                error_serializer,
                e,
            )
            raise e

        ai.track_request_finish(
            result,
            metadata,
            calling_functions,
            request_event,
            response_serializer,
            error_serializer,
        )
        return result

    wrapt.wrap_function_wrapper(klass, method_name, wrapper)
