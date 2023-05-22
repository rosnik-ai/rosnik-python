import inspect
import sys
import time

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


# Define a wrapper function that takes a custom function as an argument
def wrap_class_method(wrapped_func, prompthq_metadata):
    def wrapper(*args, **kwargs):
        # Do something before the method is called
        print("Before calling the method")

        # Call the custom function
        print("Prep for ingest request:", kwargs)
        start_time = time.time()
        result = wrapped_func(*args, **kwargs)
        end_time = time.time()
        print("Send to ingest response:", result)

        limited_frames = get_stack_frames(5)
        calling_functions = [frame.f_code.co_name for frame in limited_frames]
        collector.capture_data(
            kwargs, result, calling_functions, start_time, end_time, prompthq_metadata
        )

        # Do something after the method is called
        print("After calling the method")

        # Return the result
        return result

    # Return the wrapped function as a class method
    return wrapper
