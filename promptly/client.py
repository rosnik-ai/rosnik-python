openai_enabled = False

try:
    import openai
    openai_enabled = True
    from promptly.platforms import openai as promptly_openai
except ImportError:
    print("Skipping openai instrumentation.")

def init(api_key):
    if openai_enabled:
        promptly_openai._patch_openai()