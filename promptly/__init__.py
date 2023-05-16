openai_enabled = False

try:
    import openai
    openai_enabled = True
    import platforms.openai
except ImportError:
    print("Skipping openai instrumentation.")

def init(api_key):
    if openai_enabled:
        platforms.openai._patch_openai()