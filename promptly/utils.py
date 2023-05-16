import inspect

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
        outer_frames = inspect.getouterframes(inspect.currentframe())
        # Get the first 5~ frames for fingerprinting
        limited_frames = outer_frames[:5]
        calling_functions = [outer_frame.function for outer_frame in limited_frames]
        print(calling_functions)

        # Do something after the method is called
        print("After calling the method")

        # Return the result 
        return result

    # Return the wrapped function as a class method
    return classmethod(wrapper)
