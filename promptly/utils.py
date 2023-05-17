import inspect
import sys


def getStackFrame(num, useGetFrame=True):
    """
    https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116
    Brief:
        Gets a stack frame with the passed in num on the stack.
            If useGetFrame, uses sys._getframe (implementation detail of Cython)
                Otherwise or if sys._getframe is missing, uses inspect.stack() (which is really slow).
    """
    # Not all versions of python have the sys._getframe() method.
    # All should have inspect, though it is really slow
    if useGetFrame and hasattr(sys, "_getframe"):
        print("using get frame")
        frame = sys._getframe(0)
        frames = [frame]

        while frame.f_back is not None and len(frames) <= num:
            frames.append(frame.f_back)
            frame = frame.f_back

        return frames
    else:
        print("using inspect")
        return inspect.stack()[:num]


def getThisStackFrame(useGetFrame=True):
    """
    Brief:
        Returns the current stack frame
    """
    try:
        return getStackFrame(2, useGetFrame)
    except:
        return getStackFrame(1, useGetFrame)


# Define a wrapper function that takes a custom function as an argument
def wrap_class_method(cls, wrapped_func):
    def wrapper(*args, **kwargs):
        # Do something before the method is called
        print("Before calling the method")

        # Call the custom function
        print("Prep for ingest request:", kwargs)
        result = wrapped_func(*args, **kwargs)
        print("Send to ingest response:", result)

        # TODO: this can likely be cached in some way.
        # Or if we can have devs predefine mappings (somehow)
        # then it'll be instant.
        # Disable context so it's a bit faster
        # inspect.stack is slow. Replace with: https://gist.github.com/csm10495/39dde7add5f1b1e73c4e8299f5df1116
        # outer_frames = inspect.stack(context=0)
        outer_frames = getStackFrame(5)
        # Get the first 5~ frames for fingerprinting
        # limited_frames = outer_frames[:5]
        calling_functions = [outer_frame.function for outer_frame in limited_frames]
        print(calling_functions)

        # Do something after the method is called
        print("After calling the method")

        # Return the result
        return result

    # Return the wrapped function as a class method
    return classmethod(wrapper)
